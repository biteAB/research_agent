<template>
  <div class="search-box">
    <h1>深度研究助手</h1>
    <p class="subtitle">输入研究主题，AI 将自动为你完成规划、搜索、总结并生成完整报告</p>
    <div class="input-wrapper">
      <textarea
        v-model="topic"
        :placeholder="placeholder"
        :disabled="disabled"
        @keyup.enter.ctrl="handleSearch"
      />
      <button :disabled="disabled || !topic.trim()" @click="handleSearch">
        {{ disabled ? '研究中...' : '开始研究' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  disabled: boolean
}

defineProps<Props>()
const emit = defineEmits<{
  search: [topic: string]
}>()

const topic = ref('')
const placeholder = '例如：LangChain 框架最新发展趋势\n人工智能对软件开发的影响\n...'

const handleSearch = () => {
  const trimmed = topic.value.trim()
  if (trimmed) {
    emit('search', trimmed)
  }
}
</script>

<style scoped>
.search-box {
  max-width: 800px;
  margin: 100px auto 0;
  padding: 40px;
  text-align: center;
}

h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 12px;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
  margin-bottom: 40px;
  line-height: 1.6;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

textarea {
  width: 100%;
  min-height: 120px;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  resize: vertical;
  transition: border-color 0.2s;
}

textarea:focus {
  outline: none;
  border-color: #42b983;
}

textarea:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

button {
  align-self: center;
  padding: 14px 48px;
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  background: #42b983;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

button:hover:not(:disabled) {
  background: #359469;
  transform: translateY(-2px);
}

button:disabled {
  background: #a5d9c2;
  cursor: not-allowed;
}
</style>
