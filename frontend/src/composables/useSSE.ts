import { ref } from 'vue'
import type { AgentEvent } from '../types'

/** Options passed to sendMessage */
export interface SSECallbacks {
  onStart?: (conversationId: string) => void
  onDelta?: (delta: string) => void
  onEnd?: (reason: string) => void
  onError?: (code: number, message: string) => void
}

/** Parsed internal representation of one SSE event block */
interface ParsedEvent {
  eventType: string
  data: AgentEvent
}

/**
 * Composable that manages a single POST-based SSE connection.
 *
 * Because the backend uses POST for streaming, we use fetch + ReadableStream
 * and manually parse SSE frames.
 */
export function useSSE() {
  const isStreaming = ref(false)
  const error = ref<string | null>(null)
  const abortController = ref<AbortController | null>(null)

  /**
   * Send a message and stream the response via SSE.
   * Resolves when the stream ends or fails.
   */
  async function sendMessage(
    message: string,
    conversationId?: string,
    callbacks?: SSECallbacks,
  ): Promise<void> {
    if (isStreaming.value) return

    abortController.value = new AbortController()
    isStreaming.value = true
    error.value = null

    try {
      const response = await fetch('/agent/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer 8d3f4bd6a70a4cb89c49f6a1b0f0d5d2',
        },
        body: JSON.stringify({
          message,
          conversation_id: conversationId || undefined,
        }),
        signal: abortController.value.signal,
      })

      if (!response.ok) {
        const text = await response.text().catch(() => '')
        throw new Error(
          `HTTP ${response.status}: ${response.statusText}${text ? ` — ${text}` : ''}`,
        )
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Normalise \r\n → \n (EventSourceResponse uses \r\n line endings).
        const normalised = buffer.replace(/\r\n/g, '\n')
        const parts = normalised.split('\n\n')
        // Keep the last (possibly incomplete) chunk in the buffer
        buffer = parts.pop() || ''

        for (const part of parts) {
          const parsed = parseSSEEvent(part)
          if (!parsed) continue
          dispatchEvent(parsed, callbacks)
        }
      }

      // Flush remaining buffer
      if (buffer.trim()) {
        const parsed = parseSSEEvent(buffer)
        if (parsed) {
          dispatchEvent(parsed, callbacks)
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return
      const msg = err.message || '网络错误'
      error.value = msg
      callbacks?.onError?.(0, msg)
    } finally {
      isStreaming.value = false
    }
  }

  /** Cancel an in-flight stream */
  function cancel(): void {
    abortController.value?.abort()
    isStreaming.value = false
  }

  return { isStreaming, error, sendMessage, cancel }
}

/* ------------------------------------------------------------------ */
/*  Internal helpers                                                    */
/* ------------------------------------------------------------------ */

function parseSSEEvent(text: string): ParsedEvent | null {
  const lines = text.trim().split('\n')
  let eventType = ''
  let dataStr = ''

  for (const line of lines) {
    if (line.startsWith('event: ')) {
      eventType = line.slice(7).trim()
    } else if (line.startsWith('data: ')) {
      dataStr = line.slice(6).trim()
    }
  }

  if (!eventType || !dataStr) return null

  try {
    const parsed = JSON.parse(dataStr)
    return {
      eventType,
      data: {
        id: parsed.id,
        timestamp: parsed.timestamp,
        payload: parsed.payload,
      },
    }
  } catch {
    return null
  }
}

function dispatchEvent(parsed: ParsedEvent, callbacks?: SSECallbacks): void {
  if (!callbacks) return

  const { eventType, data } = parsed

  switch (eventType) {
    case 'conversation.start':
      callbacks.onStart?.(data.payload.conversation_id!)
      break
    case 'message.delta':
      callbacks.onDelta?.(data.payload.delta!)
      break
    case 'conversation.end':
      callbacks.onEnd?.(data.payload.reason!)
      break
    case 'error':
      callbacks.onError?.(data.payload.code!, data.payload.message!)
      break
  }
}
