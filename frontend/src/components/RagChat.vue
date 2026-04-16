<template>
  <main class="rag-page">
    <section class="rag-intro">
      <div>
        <p class="eyebrow">Local Knowledge Base</p>
        <h1>本地知识库问答</h1>
        <p class="intro-text">
          只检索已经确认入库的 Markdown 报告。回答会结合 Milvus 召回结果生成，并实时流式返回。
        </p>
      </div>
    </section>

    <section class="chat-shell">
      <div ref="messagePanel" class="messages">
        <div v-if="messages.length === 0" class="empty-state">
          <p>还没有对话</p>
          <span>先在“深度研究”里生成报告并确认入库，然后在这里提问。</span>
        </div>

        <article
          v-for="(message, index) in messages"
          :key="index"
          :class="['message', message.role]"
        >
          <div class="message-role">
            {{ message.role === 'user' ? '你' : '知识库助手' }}
          </div>

          <div
            v-if="message.role === 'assistant'"
            class="message-content markdown-body"
            v-html="renderMarkdown(message.content || '正在生成...')"
          ></div>
          <div v-else class="message-content user-text">
            {{ message.content }}
          </div>
        </article>
      </div>

      <form class="ask-form" @submit.prevent="handleAsk">
        <label class="input-label" for="rag-question">向本地知识库提问</label>
        <textarea
          id="rag-question"
          v-model="question"
          placeholder="例如：bin哥是谁？bin哥是不是世一上？"
          :disabled="isAnswering"
          @keydown.ctrl.enter.prevent="handleAsk"
        />
        <div class="actions">
          <button type="submit" :disabled="isAnswering || !question.trim()">
            {{ isAnswering ? '回答中...' : '发送问题' }}
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
import { nextTick, ref, watch } from 'vue'
import { marked } from 'marked'
import { useRagChat } from '../composables/useRagChat'

const question = ref('')
const messagePanel = ref<HTMLElement | null>(null)
const { messages, isAnswering, error, ask, clear } = useRagChat()

marked.setOptions({
  gfm: true,
  breaks: true,
})

const renderMarkdown = (content: string): string => {
  return marked.parse(content) as string
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagePanel.value) {
    messagePanel.value.scrollTop = messagePanel.value.scrollHeight
  }
}

watch(messages, scrollToBottom, { deep: true })

const handleAsk = () => {
  ask(question.value)
  question.value = ''
}
</script>

<style scoped>
.rag-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 44px 24px 64px;
}

.rag-intro {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 24px;
  align-items: end;
  margin-bottom: 22px;
}

.eyebrow {
  margin-bottom: 8px;
  color: #2f7d32;
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
}

.rag-intro h1 {
  color: #18211d;
  font-size: 2.1rem;
  line-height: 1.2;
  margin-bottom: 10px;
}

.intro-text {
  max-width: 720px;
  color: #58655f;
  line-height: 1.7;
}


.chat-shell {
  display: grid;
  gap: 16px;
}

.messages {
  min-height: 420px;
  max-height: 620px;
  overflow-y: auto;
  padding: 22px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #dde6e0;
  border-radius: 8px;
  box-shadow: 0 18px 42px rgba(31, 49, 38, 0.08);
}

.empty-state {
  min-height: 360px;
  display: grid;
  place-content: center;
  gap: 8px;
  text-align: center;
  color: #708078;
}

.empty-state p {
  color: #26332d;
  font-size: 1.1rem;
  font-weight: 700;
}

.message {
  width: 100%;
  margin-bottom: 18px;
}

.message:last-child {
  margin-bottom: 0;
}

.message-role {
  margin-bottom: 7px;
  color: #65746d;
  font-size: 0.84rem;
  font-weight: 700;
}

.message.user {
  display: grid;
  justify-items: end;
}

.message.user .message-role {
  padding-right: 4px;
}

.message-content {
  max-width: min(780px, 100%);
  line-height: 1.75;
  padding: 14px 16px;
  border-radius: 8px;
  color: #1f2b25;
}

.message.user .message-content {
  background: #2f7d32;
  color: white;
  box-shadow: 0 12px 24px rgba(47, 125, 50, 0.16);
}

.message.assistant .message-content {
  background: #f7faf8;
  border: 1px solid #e2ebe5;
}

.user-text {
  white-space: pre-wrap;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  color: #18211d;
  line-height: 1.35;
  margin: 1rem 0 0.55rem;
}

.markdown-body :deep(h1:first-child),
.markdown-body :deep(h2:first-child),
.markdown-body :deep(h3:first-child),
.markdown-body :deep(p:first-child) {
  margin-top: 0;
}

.markdown-body :deep(h1) {
  font-size: 1.35rem;
}

.markdown-body :deep(h2) {
  font-size: 1.18rem;
}

.markdown-body :deep(h3) {
  font-size: 1.04rem;
}

.markdown-body :deep(p) {
  margin: 0.7rem 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.7rem 0;
  padding-left: 1.35rem;
}

.markdown-body :deep(li) {
  margin: 0.3rem 0;
}

.markdown-body :deep(a) {
  color: #236c31;
  font-weight: 600;
  text-decoration: none;
  border-bottom: 1px solid rgba(35, 108, 49, 0.35);
}

.markdown-body :deep(a:hover) {
  border-bottom-color: #236c31;
}

.markdown-body :deep(blockquote) {
  margin: 0.85rem 0;
  padding: 0.75rem 0.9rem;
  border-left: 4px solid #86b98f;
  background: #edf6ef;
  color: #44524b;
}

.markdown-body :deep(code) {
  padding: 2px 6px;
  border-radius: 4px;
  background: #eaf0ed;
  font-size: 0.92em;
}

.markdown-body :deep(pre) {
  margin: 0.85rem 0;
  padding: 14px;
  overflow-x: auto;
  border-radius: 8px;
  background: #17231d;
  color: #eef7f0;
}

.markdown-body :deep(pre code) {
  padding: 0;
  background: transparent;
  color: inherit;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.9rem 0;
  overflow: hidden;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 9px 10px;
  border: 1px solid #d9e4dd;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #eef7f0;
}

.ask-form {
  padding: 18px;
  background: white;
  border: 1px solid #dde6e0;
  border-radius: 8px;
  box-shadow: 0 12px 30px rgba(31, 49, 38, 0.06);
}

.input-label {
  display: block;
  margin-bottom: 8px;
  color: #26332d;
  font-size: 0.9rem;
  font-weight: 700;
}

textarea {
  width: 100%;
  min-height: 112px;
  padding: 14px;
  border: 1px solid #cfdcd4;
  border-radius: 8px;
  background: #fbfdfb;
  color: #1f2b25;
  font-size: 1rem;
  line-height: 1.6;
  resize: vertical;
}

textarea:focus {
  outline: none;
  border-color: #2f7d32;
  box-shadow: 0 0 0 3px rgba(47, 125, 50, 0.12);
}

textarea:disabled {
  background: #f1f5f2;
  cursor: not-allowed;
}

.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 12px;
}

button {
  min-height: 40px;
  padding: 10px 20px;
  border: 1px solid #2f7d32;
  border-radius: 8px;
  background: #2f7d32;
  color: white;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, transform 0.2s;
}

button:hover:not(:disabled) {
  background: #256c2a;
  border-color: #256c2a;
  transform: translateY(-1px);
}

button.secondary {
  background: white;
  border-color: #cfdcd4;
  color: #34433b;
}

button.secondary:hover:not(:disabled) {
  background: #f1f6f2;
  border-color: #b9c9c0;
}

button:disabled {
  background: #a8d7b0;
  border-color: #a8d7b0;
  cursor: not-allowed;
}

.error-text {
  padding: 12px 14px;
  border-radius: 8px;
  background: #fff1f0;
  border: 1px solid #ffd4d0;
  color: #b3261e;
}

@media (max-width: 760px) {
  .rag-page {
    padding: 28px 14px 44px;
  }

  .rag-intro {
    grid-template-columns: 1fr;
  }

  .intro-notes {
    justify-content: flex-start;
  }

  .rag-intro h1 {
    font-size: 1.65rem;
  }

  .messages {
    padding: 14px;
    max-height: 560px;
  }

  .message.user {
    justify-items: stretch;
  }

  .message-content {
    max-width: 100%;
  }
}
</style>
