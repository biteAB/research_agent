<template>
  <div class="app">
    <AppNav v-model:active-page="activePage" />

    <template v-if="activePage === 'research'">
      <SearchBox
        :disabled="isRunning"
        @search="handleStartSearch"
      />
      <ResearchModal
        :visible="isRunning || (!!report && report.length > 0)"
        :is-running="isRunning"
        :current-status="currentStatus"
        :current-task-title="currentTaskTitle"
        :expanded-task-id="expandedTaskId"
        :todos="todos"
        :report="report"
        :report-id="reportId"
        :is-indexed="isIndexed"
        :is-indexing="isIndexing"
        :index-error="indexError"
        :error="error"
        :get-task-status="getTaskStatus"
        :get-task-summary="getTaskSummary"
        @close="handleClose"
        @toggle-expand="handleToggleExpand"
        @confirm-index="confirmIndex"
      />
    </template>

    <RagChat v-else />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useResearch } from './composables/useResearch'
import AppNav from './components/AppNav.vue'
import RagChat from './components/RagChat.vue'
import SearchBox from './components/SearchBox.vue'
import ResearchModal from './components/ResearchModal.vue'

const activePage = ref<'research' | 'rag'>('research')

const {
  isRunning,
  currentStatus,
  expandedTaskId,
  currentTaskTitle,
  todos,
  report,
  reportId,
  isIndexed,
  isIndexing,
  indexError,
  error,
  startResearch,
  confirmIndex,
  reset,
  getTaskStatus,
  getTaskSummary,
  toggleTaskExpand,
} = useResearch()

const handleStartSearch = async (topic: string) => {
  await startResearch(topic)
}

const handleClose = () => {
  reset()
}

const handleToggleExpand = (taskId: string) => {
  toggleTaskExpand(taskId)
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: #f5f5f5;
}
</style>
