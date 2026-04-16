<template>
  <main class="research-home">
    <section class="intro">
      <p class="eyebrow">Deep Research</p>
      <h1>深度研究助手</h1>
      <p class="subtitle">
        输入研究主题，Agent 会自动规划任务、检索资料、整理要点，并生成可下载的 Markdown 报告。
      </p>
    </section>

    <section class="research-panel">
      <label for="research-topic">研究主题</label>
      <textarea
        id="research-topic"
        v-model="topic"
        :placeholder="placeholder"
        :disabled="disabled"
        @keyup.enter.ctrl="handleSearch"
      />
      <div class="panel-footer">
        <span>按 Ctrl + Enter 也可以开始研究</span>
        <button :disabled="disabled || !topic.trim()" @click="handleSearch">
          {{ disabled ? '研究中...' : '开始研究' }}
        </button>
      </div>
    </section>

    <section class="flow-notes" aria-label="工作流说明">
      <div>
        <strong>1. 生成报告</strong>
        <span>Agent直接在页面中流式产出Markdown报告。</span>
      </div>
      <div>
        <strong>2. 确认入库</strong>
        <span>确认后才写入本地知识库。</span>
      </div>
      <div>
        <strong>3. RAG问答</strong>
        <span>从Milvus检索并流式回答。</span>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  disabled: boolean
}

defineProps<Props>()
const emit = defineEmits<{
  search: [topic: string]
}>()

const topic = ref('')
const placeholder = '例如：\n杀戮尖塔2猎人该怎么玩？有什么流派？\n炫神为什么封杀切片？\n'

const handleSearch = () => {
  const trimmed = topic.value.trim()
  if (trimmed) {
    emit('search', trimmed)
  }
}
</script>

<style scoped>
.research-home {
  max-width: 980px;
  margin: 0 auto;
  padding: 72px 24px 64px;
}

.intro {
  max-width: 760px;
  margin-bottom: 28px;
}

.eyebrow {
  margin-bottom: 8px;
  color: #2f7d32;
  font-size: 0.82rem;
  font-weight: 800;
  text-transform: uppercase;
}

h1 {
  color: #18211d;
  font-size: 2.7rem;
  line-height: 1.15;
  margin-bottom: 14px;
}

.subtitle {
  color: #58655f;
  font-size: 1.08rem;
  line-height: 1.75;
}

.research-panel {
  padding: 22px;
  background: white;
  border: 1px solid #dce8df;
  border-radius: 8px;
  box-shadow: 0 18px 42px rgba(31, 49, 38, 0.08);
}

label {
  display: block;
  margin-bottom: 10px;
  color: #26332d;
  font-size: 0.94rem;
  font-weight: 800;
}

textarea {
  width: 100%;
  min-height: 150px;
  padding: 16px;
  border: 1px solid #cfdcd4;
  border-radius: 8px;
  background: #fbfdfb;
  color: #1f2b25;
  font-size: 1rem;
  line-height: 1.65;
  resize: vertical;
  transition: border-color 0.2s, box-shadow 0.2s;
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

.panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.panel-footer span {
  color: #76847d;
  font-size: 0.9rem;
}

button {
  min-height: 42px;
  padding: 11px 28px;
  border: 1px solid #2f7d32;
  border-radius: 8px;
  background: #2f7d32;
  color: white;
  font-size: 1rem;
  font-weight: 800;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, transform 0.2s;
}

button:hover:not(:disabled) {
  background: #256c2a;
  border-color: #256c2a;
  transform: translateY(-1px);
}

button:disabled {
  background: #a8d7b0;
  border-color: #a8d7b0;
  cursor: not-allowed;
}

.flow-notes {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.flow-notes div {
  padding: 16px;
  border: 1px solid #dce8df;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
}

.flow-notes strong {
  display: block;
  margin-bottom: 6px;
  color: #26332d;
}

.flow-notes span {
  color: #64736b;
  font-size: 0.92rem;
  line-height: 1.55;
}

@media (max-width: 760px) {
  .research-home {
    padding: 42px 14px 48px;
  }

  h1 {
    font-size: 2rem;
  }

  .research-panel {
    padding: 16px;
  }

  .panel-footer {
    align-items: stretch;
    flex-direction: column;
  }

  button {
    width: 100%;
  }

  .flow-notes {
    grid-template-columns: 1fr;
  }
}
</style>
