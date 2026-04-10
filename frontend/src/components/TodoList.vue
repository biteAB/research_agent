<template>
  <div class="todo-list">
    <h3>研究计划</h3>
    <div class="tasks">
      <div
        v-for="task in todos"
        :key="task.id"
        class="task-item"
        :class="getStatus(task.id)"
      >
        <div class="task-status">
          <span class="status-dot"></span>
        </div>
        <div class="task-content">
          <div class="task-title">{{ task.title }}</div>
          <div class="task-intent">{{ task.intent }}</div>
          <div v-if="getStatus(task.id) === 'done'" class="task-queries">
            <span v-for="q in task.search_queries" :key="q" class="query-tag">
              {{ q }}
            </span>
          </div>
        </div>
        <div class="task-status-label">
          {{ getStatusLabel(getStatus(task.id)) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TodoTask, TaskStatus } from '../composables/useResearch'

interface Props {
  todos: TodoTask[]
  getTaskStatus: (taskId: string) => TaskStatus
}

const props = defineProps<Props>()

const statusLabels: Record<TaskStatus, string> = {
  pending: '等待中',
  planning: '规划中',
  searching: '搜索中',
  summarizing: '总结中',
  done: '已完成',
  error: '出错了',
}

const getStatus = (taskId: string): TaskStatus => {
  return props.getTaskStatus(taskId)
}

const getStatusLabel = (status: TaskStatus): string => {
  return statusLabels[status]
}
</script>

<style scoped>
.todo-list {
  margin-bottom: 24px;
}

h3 {
  font-size: 1.2rem;
  margin-bottom: 16px;
  color: #333;
}

.tasks {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #ddd;
  transition: all 0.2s;
}

.task-item.pending {
  opacity: 0.5;
  border-left-color: #ddd;
}

.task-item.searching {
  background: #fff3cd;
  border-left-color: #ffc107;
  opacity: 1;
}

.task-item.summarizing {
  background: #cce5ff;
  border-left-color: #007bff;
  opacity: 1;
}

.task-item.done {
  background: #d4edda;
  border-left-color: #28a745;
  opacity: 1;
}

.task-item.error {
  background: #f8d7da;
  border-left-color: #dc3545;
  opacity: 1;
}

.status-dot {
  display: block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ddd;
}

.task-item.searching .status-dot {
  background: #ffc107;
  animation: pulse 1.5s infinite;
}

.task-item.summarizing .status-dot {
  background: #007bff;
  animation: pulse 1.5s infinite;
}

.task-item.done .status-dot {
  background: #28a745;
}

.task-item.error .status-dot {
  background: #dc3545;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.task-content {
  flex: 1;
}

.task-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.task-intent {
  font-size: 0.85rem;
  color: #666;
}

.task-queries {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.query-tag {
  font-size: 0.75rem;
  padding: 2px 8px;
  background: #e9ecef;
  border-radius: 4px;
  color: #495057;
}

.task-status-label {
  font-size: 0.8rem;
  color: #666;
  font-weight: 500;
}
</style>
