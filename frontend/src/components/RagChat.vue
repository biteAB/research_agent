<template>
  <main class="rag-page">
    <section class="rag-intro">
      <h1>本地知识库问答</h1>
      <p>只检索你确认入库的 Markdown 报告，回答会实时流式生成。</p>
    </section>

    <section class="chat-shell">
      <div class="messages">
        <div v-if="messages.length === 0" class="empty-state">
          先在“深度研究”里生成报告并确认入库，然后在这里提问。
        </div>
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['message', message.role]"
        >
          <div class="message-role">{{ message.role === 'user' ? '你' : '知识库助手' }}</div>
          <div class="message-content">{{ message.content || '正在生成...' }}</div>
        </div>
      </div>

      <form class="ask-form" @submit.prevent="handleAsk">
        <textarea
          v-model="question"
          placeholder="请输入你想询问本地知识库的问题"
          :disabled="isAnswering"
        />
        <div class="actions">
          <button type="submit" :disabled="isAnswering || !question.trim()">
            {{ isAnswering ? '回答中...' : '提问' }}
          </button>
          <button type="button" class="secondary" @click="clear">
            清空当前对话
          </button>
        </div>
      </form>

      <p v-if="error" class="error-text">{{ error }}</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRagChat } from '../composables/useRagChat'

const question = ref('')
const { messages, isAnswering, error, ask, clear } = useRagChat()

const handleAsk = () => {
  ask(question.value)
  question.value = ''
}
</script>

<style scoped>
.rag-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 56px 24px;
}

.rag-intro {
  margin-bottom: 24px;
}

.rag-intro h1 {
  color: #263238;
  font-size: 2rem;
  margin-bottom: 8px;
}

.rag-intro p {
  color: #607d8b;
  line-height: 1.6;
}

.chat-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.messages {
  min-height: 360px;
  max-height: 560px;
  overflow-y: auto;
  padding: 18px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.empty-state {
  color: #78909c;
  text-align: center;
  padding: 120px 16px;
}

.message {
  margin-bottom: 16px;
}

.message-role {
  margin-bottom: 6px;
  color: #607d8b;
  font-size: 0.85rem;
  font-weight: 600;
}

.message-content {
  white-space: pre-wrap;
  line-height: 1.7;
  padding: 12px 14px;
  border-radius: 8px;
}

.message.user .message-content {
  color: #263238;
  background: #edf7ed;
}

.message.assistant .message-content {
  color: #263238;
  background: #f6f8f9;
}

.ask-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

textarea {
  width: 100%;
  min-height: 108px;
  padding: 14px;
  border: 1px solid #d6d6d6;
  border-radius: 8px;
  font-size: 1rem;
  resize: vertical;
}

textarea:focus {
  outline: none;
  border-color: #2f7d32;
}

.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

button {
  padding: 10px 22px;
  border: none;
  border-radius: 8px;
  background: #2f7d32;
  color: white;
  cursor: pointer;
}

button.secondary {
  background: #eceff1;
  color: #37474f;
}

button:disabled {
  background: #a5d9c2;
  cursor: not-allowed;
}

.error-text {
  color: #b3261e;
}
</style>
