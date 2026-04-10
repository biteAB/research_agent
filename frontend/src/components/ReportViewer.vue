<template>
  <div class="report-viewer">
    <h3>研究报告</h3>
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
</script>

<style scoped>
.report-viewer {
  margin-top: 24px;
}

h3 {
  font-size: 1.2rem;
  margin-bottom: 16px;
  color: #333;
}

.report-content {
  background: white;
  padding: 24px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  max-height: 500px;
  overflow-y: auto;
  line-height: 1.7;
}

.report-content :deep(h1) {
  font-size: 1.8rem;
  margin-bottom: 1rem;
  border-bottom: 2px solid #eee;
  padding-bottom: 0.5rem;
}

.report-content :deep(h2) {
  font-size: 1.4rem;
  margin: 1.5rem 0 1rem;
  color: #2c3e50;
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
  color: #42b983;
  text-decoration: none;
}

.report-content :deep(a:hover) {
  text-decoration: underline;
}

.report-content :deep(pre) {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  margin: 1rem 0;
}

.report-content :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.9em;
}

.report-content :deep(blockquote) {
  border-left: 4px solid #ddd;
  padding-left: 1rem;
  color: #666;
  margin: 1rem 0;
}

.placeholder {
  background: #f8f9fa;
  padding: 48px;
  border-radius: 8px;
  text-align: center;
  color: #666;
  border: 2px dashed #ddd;
}
</style>
