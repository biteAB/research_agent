<template>
  <div class="todo-list">
    <h3>研究计划</h3>
    <div class="tasks">
      <div
        v-for="task in todos"
        :key="task.id"
        class="task-item"
        :class="[getStatus(task.id), { expanded: expandedTaskId === task.id }]"
        @click="handleClick(task.id)"
      >
        <div class="task-header">
          <div class="task-status">
            <span class="status-dot"></span>
          </div>
          <div class="task-content">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-intent">{{ task.intent }}</div>
          </div>
          <div class="task-status-label">
            {{ getStatusLabel(getStatus(task.id)) }}
          </div>
          <div class="expand-icon">
            <span :class="['arrow', expandedTaskId === task.id ? 'expanded' : '']">▼</span>
          </div>
        </div>
        <div v-if="expandedTaskId === task.id" class="task-details">
          <div class="detail-section">
            <h4>研究目的</h4>
            <p>{{ task.intent }}</p>
          </div>
          <div class="detail-section">
            <h4>搜索关键词</h4>
            <div class="search-queries">
              <span v-for="q in task.search_queries" :key="q" class="query-tag">
                {{ q }}
              </span>
            </div>
          </div>
          <div v-if="getTaskSummary(task.id)" class="detail-section">
            <h4>研究总结</h4>
            <div class="summary-content">
              {{ getTaskSummary(task.id)!.summary }}
            </div>
          </div>
          <div v-if="getTaskSummary(task.id) && getTaskSummary(task.id)!.key_points.length > 0" class="detail-section">
            <h4>要点总结</h4>
            <ul class="key-points">
              <li v-for="(point, index) in getTaskSummary(task.id)!.key_points" :key="index">
                {{ point }}
              </li>
            </ul>
          </div>
          <div v-if="getTaskSummary(task.id) && getTaskSummary(task.id)!.sources.length > 0" class="detail-section">
            <h4>参考来源</h4>
            <ul class="sources">
              <li v-for="(source, index) in getTaskSummary(task.id)!.sources" :key="index">
                <a :href="source" target="_blank" rel="noopener noreferrer">{{ source }}</a>
              </li>
            </ul>
          </div>
          <div v-if="getStatus(task.id) === 'searching'" class="detail-section status-info">
            <div class="loading">正在搜索中...</div>
          </div>
          <div v-if="getStatus(task.id) === 'summarizing'" class="detail-section status-info">
            <div class="loading">正在生成总结中...</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TodoTask, TaskStatus, TaskSummary } from '../composables/useResearch'

interface Props {
  todos: TodoTask[]
  expandedTaskId: string | null
  getTaskStatus: (taskId: string) => TaskStatus
  getTaskSummary: (taskId: string) => TaskSummary | undefined
}

const props = defineProps<Props>()
const emit = defineEmits<{
  toggleExpand: [taskId: string]
}>()

const statusLabels: Record<TaskStatus, string> = {
  pending: '等待中',
  planning: '规划中',
  searching: '搜索中',
  summarizing: '总结中',
  reporting: '报告生成中',
  done: '已完成',
  error: '出错了',
}

const getStatus = (taskId: string): TaskStatus => {
  return props.getTaskStatus(taskId)
}

const getStatusLabel = (status: TaskStatus): string => {
  return statusLabels[status]
}

const getTaskSummary = (taskId: string): TaskSummary | undefined => {
  return props.getTaskSummary(taskId)
}

const handleClick = (taskId: string) => {
  emit('toggleExpand', taskId)
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
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #ddd;
  transition: all 0.2s;
  cursor: pointer;
  overflow: hidden;
}

.task-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

.task-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
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

.task-status-label {
  font-size: 0.8rem;
  color: #666;
  font-weight: 500;
}

.expand-icon {
  width: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.expand-icon .arrow {
  font-size: 10px;
  color: #999;
  transition: transform 0.2s;
  display: block;
}

.expand-icon .arrow.expanded {
  transform: rotate(180deg);
}

.task-details {
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  padding: 16px;
  background: rgba(255, 255, 255, 0.5);
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  font-size: 0.9rem;
  color: #555;
  margin-bottom: 8px;
  font-weight: 600;
}

.detail-section p {
  margin: 0;
  color: #444;
  line-height: 1.6;
}

.search-queries {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.query-tag {
  font-size: 0.8rem;
  padding: 4px 10px;
  background: #e9ecef;
  border-radius: 4px;
  color: #495057;
}

.summary-content {
  line-height: 1.6;
  color: #444;
  white-space: pre-wrap;
}

.key-points {
  margin: 0;
  padding-left: 20px;
  line-height: 1.6;
}

.key-points li {
  margin-bottom: 4px;
  color: #444;
}

.sources {
  margin: 0;
  padding-left: 20px;
  line-height: 1.5;
}

.sources a {
  color: #007bff;
  text-decoration: none;
}

.sources a:hover {
  text-decoration: underline;
}

.status-info {
  text-align: center;
  padding: 12px;
}

.loading {
  color: #666;
  animation: pulse 1.5s infinite;
}
</style>
