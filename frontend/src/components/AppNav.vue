<template>
  <header class="app-nav">
    <div class="brand">
      <strong>Research Agent</strong>
      <span>本地知识闭环</span>
    </div>
    <nav>
      <button
        :class="{ active: activePage === 'research' }"
        @click="setPage('research')"
      >
        深度研究
      </button>
      <button
        :class="{ active: activePage === 'rag' }"
        @click="setPage('rag')"
      >
        知识库问答
      </button>
    </nav>
  </header>
</template>

<script setup lang="ts">
type AppPage = 'research' | 'rag'

interface Props {
  activePage: AppPage
}

defineProps<Props>()

const emit = defineEmits<{
  'update:activePage': [page: AppPage]
}>()

const setPage = (page: AppPage) => {
  emit('update:activePage', page)
}
</script>

<style scoped>
.app-nav {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 14px 32px;
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid #e7e7e7;
}

.brand {
  display: flex;
  align-items: baseline;
  gap: 10px;
  color: #263238;
}

.brand span {
  color: #607d8b;
  font-size: 0.9rem;
}

nav {
  display: flex;
  gap: 8px;
}

button {
  padding: 8px 16px;
  border: 1px solid #d8d8d8;
  border-radius: 8px;
  background: white;
  color: #40515a;
  cursor: pointer;
}

button.active {
  background: #2f7d32;
  border-color: #2f7d32;
  color: white;
}

@media (max-width: 640px) {
  .app-nav {
    align-items: flex-start;
    flex-direction: column;
    padding: 12px 16px;
  }
}
</style>
