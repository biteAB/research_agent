<template>
  <div class="app">
    <SearchBox
      :disabled="isRunning"
      @search="handleStartSearch"
    />
    <ResearchModal
      :visible="isRunning || (!!report && report.length > 0)"
      :is-running="isRunning"
      :current-status="currentStatus"
      :current-task-title="currentTaskTitle"
      :todos="todos"
      :report="report"
      :error="error"
      :get-task-status="getTaskStatus"
      @close="handleClose"
    />
  </div>
</template>

<script setup lang="ts">
import { useResearch } from './composables/useResearch'
import SearchBox from './components/SearchBox.vue'
import ResearchModal from './components/ResearchModal.vue'

const {
  isRunning,
  currentStatus,
  currentTaskTitle,
  todos,
  report,
  error,
  startResearch,
  reset,
  getTaskStatus,
} = useResearch()

const handleStartSearch = async (topic: string) => {
  await startResearch(topic)
}

const handleClose = () => {
  reset()
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: #f5f5f5;
}
</style>
