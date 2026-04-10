<template>
  <div v-if="visible" class="modal-overlay" @click.self="handleClose">
    <div class="modal-content">
      <div class="modal-header">
        <h2>正在深度研究</h2>
        <button class="close-btn" @click="handleClose" :disabled="isRunning">
          ×
        </button>
      </div>

      <div class="current-status" v-if="currentTaskTitle">
        <span class="status-indicator" :class="currentStatus"></span>
        <span>{{ getStatusText() }}</span>
      </div>

      <div class="modal-body">
        <TodoList
          :todos="todos"
          :get-task-status="getTaskStatus"
        />

        <ReportViewer
          :report="report"
          :is-generating="currentStatus === 'reporting'"
        />
      </div>

      <div v-if="error" class="error-box">
        <strong>错误:</strong> {{ error }}
      </div>

      <div class="modal-footer" v-if="currentStatus === 'done'">
        <button class="btn-primary" @click="handleClose">完成</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TodoTask, TaskStatus } from '../composables/useResearch'
import TodoList from './TodoList.vue'
import ReportViewer from './ReportViewer.vue'

interface Props {
  visible: boolean
  isRunning: boolean
  currentStatus: TaskStatus
  currentTaskTitle: string
  todos: TodoTask[]
  report: string
  error: string | null
  getTaskStatus: (taskId: string) => TaskStatus
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

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
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 900px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.4rem;
  color: #2c3e50;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  font-size: 2rem;
  color: #999;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  border-radius: 4px;
}

.close-btn:hover:not(:disabled) {
  background: #f5f5f5;
  color: #333;
}

.close-btn:disabled {
  cursor: not-allowed;
}

.current-status {
  padding: 12px 24px;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
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

.modal-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.error-box {
  padding: 12px 24px;
  background: #f8d7da;
  color: #721c24;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #eee;
  text-align: right;
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
</style>
