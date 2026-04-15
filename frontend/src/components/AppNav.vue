<template>
  <header class="app-nav">
    <div class="brand">
      <span class="brand-mark">RA</span>
      <div>
        <strong>Research Agent</strong>
        <span>本地知识闭环</span>
      </div>
    </div>

    <nav aria-label="主导航">
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
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(206, 220, 211, 0.9);
  backdrop-filter: blur(14px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  color: #18211d;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
  border-radius: 8px;
  background: #2f7d32;
  color: white;
  font-size: 0.86rem;
  font-weight: 800;
}

.brand strong {
  display: block;
  font-size: 1rem;
  line-height: 1.2;
}

.brand span:last-child {
  display: block;
  margin-top: 2px;
  color: #64736b;
  font-size: 0.86rem;
}

nav {
  display: flex;
  gap: 8px;
  padding: 4px;
  background: #f2f7f3;
  border: 1px solid #dce8df;
  border-radius: 8px;
}

button {
  min-height: 36px;
  padding: 8px 16px;
  border: 1px solid transparent;
  border-radius: 7px;
  background: transparent;
  color: #405047;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

button:hover {
  background: white;
  border-color: #d1dfd6;
}

button.active {
  background: #2f7d32;
  border-color: #2f7d32;
  color: white;
  box-shadow: 0 8px 18px rgba(47, 125, 50, 0.18);
}

@media (max-width: 640px) {
  .app-nav {
    align-items: stretch;
    flex-direction: column;
    padding: 12px 14px;
  }

  nav {
    width: 100%;
  }

  button {
    flex: 1;
  }
}
</style>
