<script setup lang="ts">
</script>

<template>
  <aside class="sidebar">
    <!-- Header -->
    <div class="sidebar-header">
      <svg class="sidebar-logo" viewBox="0 0 24 24" width="24" height="24" fill="none"   stroke="#999" stroke-width="1.5">
        <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" stroke-linejoin="round"/>
      </svg>
      <span class="sidebar-title">Pang Agent</span>
    </div>

    <!-- New conversation button -->
    <button class="new-chat-btn">
      <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
        <path d="M8 2v12M2 8h12"/>
      </svg>
      新对话
    </button>

    <!-- Section label -->
    <div class="section-label">历史会话</div>

    <!-- Conversation list -->
    <div class="conversation-list">
      <p class="placeholder">暂无历史会话</p>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 260px;
  min-width: 260px;
  background: #f7f7f7;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e5e5e5;
  user-select: none;
}

/* -- Header -- */
.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 20px 16px;
}

.sidebar-logo {
  flex-shrink: 0;
}

.sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: 0.2px;
}

/* -- New conversation button -- */
.new-chat-btn {
  margin: 0 16px 20px;
  padding: 10px 0;
  width: calc(100% - 32px);
  border: 1px solid #ddd;
  border-radius: 10px;
  background: transparent;
  color: #666;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: background 0.15s, border-color 0.15s;
  font-family: inherit;
}

.new-chat-btn:hover {
  background: #f0f0f0;
  border-color: #ccc;
  color: #333;
}

/* -- Section label -- */
.section-label {
  padding: 0 20px 8px;
  font-size: 11px;
  font-weight: 500;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

/* -- Conversation list -- */
.conversation-list {
  flex: 1;
  padding: 0 12px;
  overflow-y: auto;
}

.placeholder {
  color: #999;
  font-size: 13px;
  text-align: center;
  margin-top: 40px;
  line-height: 1.6;
}

/* list item hover style (for future items) */
.conversation-list > *:not(.placeholder) {
  padding: 10px 8px;
  border-radius: 8px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: background 0.12s;
}

.conversation-list > *:not(.placeholder):hover {
  background: #f0f0f0;
}
</style>
