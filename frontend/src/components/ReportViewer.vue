<template>
  <div class="report-viewer">
    <div class="report-header">
      <h3>研究报告</h3>
      <div v-if="report" class="download-buttons">
        <button class="btn-download btn-markdown" @click="downloadMarkdown">
          下载 Markdown
        </button>
      </div>
    </div>
    <div
      v-if="report"
      class="report-content"
      v-html="renderedReport"
    ></div>
    <div v-else-if="isGenerating" class="placeholder">
      <p>正在生成报告，请稍候...</p>
    </div>
    <div v-else class="placeholder">
      <p>报告将在这里显示...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

interface Props {
  report: string
  isGenerating: boolean
}

const props = defineProps<Props>()

const renderedReport = computed(() => {
  return marked.parse(props.report)
})

const downloadMarkdown = () => {
  const blob = new Blob([props.report], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `research-report-${new Date().toISOString().slice(0, 10)}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.report-viewer {
  margin-top: 24px;
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.report-header h3 {
  font-size: 1.2rem;
  margin: 0;
  color: #26332d;
}

.download-buttons {
  display: flex;
  gap: 8px;
}

.btn-download {
  min-height: 36px;
  padding: 8px 14px;
  border: 1px solid #cfdcd4;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.btn-markdown {
  background: white;
  color: #34433b;
}

.btn-markdown:hover {
  background: #f1f6f2;
  border-color: #b9c9c0;
}

h3 {
  font-size: 1.2rem;
  margin-bottom: 16px;
  color: #26332d;
}

.report-content {
  background: white;
  padding: 24px;
  border-radius: 8px;
  border: 1px solid #dce8df;
  max-height: 500px;
  overflow-y: auto;
  line-height: 1.7;
  box-shadow: 0 12px 30px rgba(31, 49, 38, 0.06);
}

.report-content :deep(h1) {
  font-size: 1.8rem;
  margin-bottom: 1rem;
  color: #18211d;
  border-bottom: 2px solid #e3eee6;
  padding-bottom: 0.5rem;
}

.report-content :deep(h2) {
  font-size: 1.4rem;
  margin: 1.5rem 0 1rem;
  color: #26332d;
}

.report-content :deep(h3) {
  font-size: 1.2rem;
  margin: 1rem 0 0.5rem;
}

.report-content :deep(p) {
  margin-bottom: 1rem;
}

.report-content :deep(ul), .report-content :deep(ol) {
  margin: 1rem 0;
  padding-left: 2rem;
}

.report-content :deep(li) {
  margin-bottom: 0.5rem;
}

.report-content :deep(a) {
  color: #236c31;
  font-weight: 600;
  text-decoration: none;
}

.report-content :deep(a:hover) {
  text-decoration: underline;
}

.report-content :deep(pre) {
  background: #17231d;
  color: #eef7f0;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1rem 0;
}

.report-content :deep(code) {
  background: #eaf0ed;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

.report-content :deep(pre code) {
  padding: 0;
  background: transparent;
  color: inherit;
}

.report-content :deep(blockquote) {
  border-left: 4px solid #86b98f;
  padding-left: 1rem;
  color: #44524b;
  margin: 1rem 0;
}

.placeholder {
  background: white;
  padding: 48px;
  border-radius: 8px;
  text-align: center;
  color: #64736b;
  border: 1px dashed #b9c9c0;
}
</style>
