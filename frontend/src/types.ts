/** Payload inside every SSE data envelope */
export interface AgentEventPayload {
  conversation_id?: string
  delta?: string
  reason?: string
  code?: number
  message?: string
}

/** SSE data envelope: { id, timestamp, payload } */
export interface AgentEvent {
  id: string
  timestamp: number
  payload: AgentEventPayload
}

/** A rendered chat message */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}
