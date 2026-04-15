<template>
  <div v-if="visible" class="fullscreen-page">
    <div class="page-header">
      <div class="header-title">
        <h2>正在深度研究</h2>
        <div v-if="currentTaskTitle" class="current-status">
          <span class="status-indicator" :class="currentStatus"></span>
          <span>{{ getStatusText() }}</span>
        </div>
      </div>
      <button class="close-btn" @click="handleClose" :disabled="isRunning">
        ← 返回首页
      </button>
    </div>

    <div class="page-body">
      <div v-if="error" class="error-box">
        <strong>错误:</strong> {{ error }}
      </div>

      <TodoList
        :todos="todos"
        :expanded-task-id="expandedTaskId"
        :get-task-status="getTaskStatus"
        :get-task-summary="getTaskSummary"
        @toggle-expand="handleToggleExpand"
      />

      <ReportViewer
        :report="report"
        :is-generating="currentStatus === 'reporting'"
      />

      <div v-if="currentStatus === 'done'" class="page-footer">
        <div class="index-actions">
          <button
            class="btn-primary"
            :disabled="!reportId || isIndexed || isIndexing"
            @click="handleConfirmIndex"
          >
            {{ isIndexed ? '已入库' : isIndexing ? '正在入库...' : '确认入库' }}
          </button>
          <span v-if="isIndexed" class="success-text">这份报告已进入本地知识库</span>
          <span v-else-if="!reportId" class="muted-text">报告保存后可入库</span>
          <span v-if="indexError" class="error-text">{{ indexError }}</span>
        </div>
        <button class="btn-primary" @click="handleClose">完成并返回</button>
      </div>
    </div>
  </div>
  <div v-else class="empty-placeholder"></div>
</template>

<script setup lang="ts">
import type { TodoTask, TaskStatus, TaskSummary } from '../composables/useResearch'
import TodoList from './TodoList.vue'
import ReportViewer from './ReportViewer.vue'

interface Props {
  visible: boolean
  isRunning: boolean
  currentStatus: TaskStatus
  currentTaskTitle: string
  expandedTaskId: string | null
  todos: TodoTask[]
  report: string
  reportId: string | null
  isIndexed: boolean
  isIndexing: boolean
  indexError: string | null
  error: string | null
  getTaskStatus: (taskId: string) => TaskStatus
  getTaskSummary: (taskId: string) => TaskSummary | undefined
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  toggleExpand: [taskId: string]
  confirmIndex: []
}>()

const handleToggleExpand = (taskId: string) => {
  emit('toggleExpand', taskId)
}

const statusTextMap: Record<TaskStatus, string> = {
  pending: '准备中...',
  planning: '制定研究计划中...',
  searching: '正在搜索: ',
  summarizing: '正在总结: ',
  reporting: '正在生成最终报告...',
  done: '已完成',
  error: '出错了',
}

const getStatusText = (): string => {
  const base = statusTextMap[props.currentStatus]
  if (props.currentTaskTitle && (props.currentStatus === 'searching' || props.currentStatus === 'summarizing')) {
    return `${base}${props.currentTaskTitle}`
  }
  return base
}

const handleClose = () => {
  emit('close')
}

const handleConfirmIndex = () => {
  emit('confirmIndex')
}
</script>

<style scoped>
.fullscreen-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.page-header {
  background: white;
  border-bottom: 1px solid #eee;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-header h2 {
  margin: 0;
  font-size: 1.4rem;
  color: #2c3e50;
}

.current-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #495057;
}

.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #6c757d;
}

.status-indicator.searching,
.status-indicator.summarizing,
.status-indicator.planning,
.status-indicator.reporting {
  background: #ffc107;
  animation: pulse 1.5s infinite;
}

.status-indicator.done {
  background: #28a745;
}

.status-indicator.error {
  background: #dc3545;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.close-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 8px;
  font-size: 0.9rem;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover:not(:disabled) {
  background: #f5f5f5;
  color: #333;
  border-color: #ccc;
}

.close-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.error-box {
  padding: 12px 24px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 8px;
  margin-bottom: 16px;
}

.page-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.index-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-primary {
  padding: 10px 24px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
}

.btn-primary:hover {
  background: #359469;
}

.btn-primary:disabled {
  background: #a5d9c2;
  cursor: not-allowed;
}

.success-text {
  color: #2f7d32;
  font-size: 0.9rem;
}

.muted-text {
  color: #777;
  font-size: 0.9rem;
}

.error-text {
  color: #b3261e;
  font-size: 0.9rem;
}

.empty-placeholder {
  display: none;
}
</style>
