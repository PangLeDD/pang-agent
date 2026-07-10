<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useSSE } from '../composables/useSSE'
import type { ChatMessage } from '../types'

/* ---- state ---- */
const input = ref('')
const messages = ref<ChatMessage[]>([])
const messagesContainer = ref<HTMLElement | null>(null)

const { isStreaming, sendMessage } = useSSE()

const currentAssistantId = ref<string | null>(null)
const currentAssistantContent = ref('')
const conversationId = ref<string | null>(null)

/* ---- helpers ---- */
function uid(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

async function scrollToBottom() {
  await nextTick()
  const el = messagesContainer.value
  if (el) el.scrollTop = el.scrollHeight
}

/* ---- send ---- */
async function handleSend() {
  const text = input.value.trim()
  if (!text || isStreaming.value) return

  // push user message
  messages.value.push({
    id: uid(),
    role: 'user',
    content: text,
    timestamp: Date.now(),
  })
  input.value = ''
  await scrollToBottom()

  // prepare placeholder for the assistant response
  currentAssistantId.value = uid()
  currentAssistantContent.value = ''

  await sendMessage(text, conversationId.value ?? undefined, {
    onStart: (convId: string) => {
      conversationId.value = convId
    },

    onDelta: (delta: string) => {
      currentAssistantContent.value += delta
    },

    onEnd: () => {
      // finalize — push the completed message
      if (currentAssistantContent.value) {
        messages.value.push({
          id: currentAssistantId.value!,
          role: 'assistant',
          content: currentAssistantContent.value,
          timestamp: Date.now(),
        })
      }
      currentAssistantId.value = null
      currentAssistantContent.value = ''
    },

    onError: (code, msg) => {
      // push a visible error message
      messages.value.push({
        id: currentAssistantId.value!,
        role: 'assistant',
        content: `[错误 ${code || ''}] ${msg}`,
        timestamp: Date.now(),
      })
      currentAssistantId.value = null
      currentAssistantContent.value = ''
    },
  })

  // fallback: if onEnd was never fired but we accumulated content
  if (currentAssistantContent.value) {
    messages.value.push({
      id: currentAssistantId.value!,
      role: 'assistant',
      content: currentAssistantContent.value,
      timestamp: Date.now(),
    })
    currentAssistantId.value = null
    currentAssistantContent.value = ''
  }

  await scrollToBottom()
}

/* ---- keyboard ---- */
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function autoResize(el: HTMLTextAreaElement) {
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

/* ---- auto-scroll on new messages ---- */
watch(
  () => messages.value.length,
  () => scrollToBottom(),
)
</script>

<template>
  <div class="chat-main">
    <!-- Messages area -->
    <div ref="messagesContainer" class="messages-container">

      <!-- Empty state -->
      <div v-if="messages.length === 0 && !isStreaming" class="empty-state">
        <div class="empty-state-inner">
          <svg class="empty-logo" viewBox="0 0 48 48" width="48" height="48" fill="none" stroke="#ccc" stroke-width="1.5">
            <path d="M24 4L6 13v22l18 9 18-9V13L24 4z" stroke-linejoin="round"/>
            <path d="M24 4v40" stroke="#ddd" stroke-width="1"/>
          </svg>
          <h1 class="empty-title">Pang Agent</h1>
          <p class="empty-subtitle">我可以帮助你写作、编程、翻译、分析问题……</p>
        </div>
      </div>

      <!-- Message list -->
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="message-row"
        :class="msg.role"
      >
        <div v-if="msg.role === 'assistant'" class="avatar">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="#e0e0e0">
            <path d="M12 2L2 7v10l10 5 10-5V7L12 2z"/>
          </svg>
        </div>
        <div :class="msg.role === 'user' ? 'bubble' : 'content'">
          {{ msg.content }}
        </div>
      </div>

      <!-- Streaming placeholder -->
      <div v-if="isStreaming" class="message-row assistant">
        <div class="avatar">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="#e0e0e0">
            <path d="M12 2L2 7v10l10 5 10-5V7L12 2z"/>
          </svg>
        </div>
        <div class="content">
          <template v-if="currentAssistantContent">
            {{ currentAssistantContent }}<span class="cursor">▌</span>
          </template>
          <span v-else class="dot-pulse"><span></span><span></span><span></span></span>
        </div>
      </div>
    </div>

    <!-- Input area -->
    <div class="input-area">
      <div class="input-inner">
        <div class="input-wrapper">
          <textarea
            v-model="input"
            rows="1"
            placeholder="输入消息..."
            :disabled="isStreaming"
            @keydown="handleKeydown"
            @input="autoResize(($event.target as HTMLTextAreaElement))"
          ></textarea>
          <button
            class="send-button"
            :disabled="isStreaming || !input.trim()"
            @click="handleSend"
            title="发送"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 19V5M5 12l7-7 7 7"/>
            </svg>
          </button>
        </div>
        <p class="input-hint">Pang Agent 的回答基于公开信息，请独立判断。</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-main {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

/* ========== Messages ========== */
.messages-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 48px 0 16px;
  scroll-behavior: smooth;
}

/* -- Empty state -- */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0 24px;
  user-select: none;
}

.empty-state-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-logo {
  margin-bottom: 8px;
  opacity: 0.6;
}

.empty-title {
  font-size: 36px;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

.empty-subtitle {
  font-size: 14px;
  color: #999;
  line-height: 1.6;
  max-width: 360px;
}

/* -- Message rows -- */
.message-row {
  max-width: 768px;
  width: 100%;
  margin: 0 auto 36px;
  padding: 0 24px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-shrink: 0;
}

.message-row:last-child {
  margin-bottom: 0;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
  margin-left: max(0px, calc((100% - 768px) / 4));
}

/* -- Avatar (assistant only) -- */
.avatar {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 4px;
  opacity: 0.7;
}

/* -- User bubble -- */
.bubble {
  background: #f0f0f0;
  color: #1a1a1a;
  padding: 10px 16px;
  border-radius: 16px;
  border-bottom-right-radius: 4px;
  max-width: 70%;
  line-height: 1.7;
  font-size: 15px;
  white-space: pre-wrap;
  word-break: break-word;
}

/* -- Assistant content (no bubble) -- */
.content {
  color: #333;
  line-height: 1.7;
  font-size: 15px;
  white-space: pre-wrap;
  word-break: break-word;
  flex: 1;
  min-width: 0;
}

/* cursor blink */
.cursor {
  animation: blink 0.8s step-end infinite;
  color: #ccc;
}
@keyframes blink {
  50% { opacity: 0; }
}

/* dot pulse while waiting for first delta */
.dot-pulse {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  padding-top: 4px;
}
.dot-pulse span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ccc;
  animation: dot-bounce 1.2s ease-in-out infinite;
}
.dot-pulse span:nth-child(2) { animation-delay: 0.2s; }
.dot-pulse span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ========== Input area ========== */
.input-area {
  border-top: 1px solid #eee;
  padding-top: 12px;
  background: #ffffff;
}

.input-inner {
  max-width: 768px;
  margin: 0 auto;
  padding: 0 24px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.input-wrapper {
  width: 100%;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  padding: 8px 8px 8px 18px;
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: #4c6fff;
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #333;
  font-size: 15px;
  line-height: 1.5;
  resize: none;
  outline: none;
  max-height: 160px;
  font-family: inherit;
}

textarea::placeholder {
  color: #999;
}

textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-button {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background: #4c6fff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, opacity 0.15s;
}

.send-button:hover:not(:disabled) {
  background: #5f7dff;
}

.send-button:active:not(:disabled) {
  background: #3a5ae0;
}

.send-button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.input-hint {
  margin-top: 10px;
  font-size: 11px;
  color: #bbb;
  text-align: center;
  user-select: none;
}
</style>
