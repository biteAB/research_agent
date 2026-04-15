import { ref } from 'vue'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export function useRagChat() {
  const messages = ref<ChatMessage[]>([])
  const isAnswering = ref(false)
  const error = ref<string | null>(null)
  const eventSource = ref<EventSource | null>(null)

  const stop = () => {
    eventSource.value?.close()
    eventSource.value = null
    isAnswering.value = false
  }

  const ask = (question: string) => {
    const trimmed = question.trim()
    if (!trimmed || isAnswering.value) return

    stop()
    messages.value.push({ role: 'user', content: trimmed })
    messages.value.push({ role: 'assistant', content: '' })

    isAnswering.value = true
    error.value = null

    const url = `/api/rag/chat/stream?question=${encodeURIComponent(trimmed)}`
    eventSource.value = new EventSource(url)

    eventSource.value.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data)

        if (parsed.event === 'answer_chunk') {
          const last = messages.value[messages.value.length - 1]
          if (last?.role === 'assistant') {
            last.content += parsed.data.chunk
          }
        }

        if (parsed.event === 'done') {
          stop()
        }

        if (parsed.event === 'error') {
          error.value = parsed.data.message
          stop()
        }
      } catch (e) {
        error.value = e instanceof Error ? e.message : '解析回答失败'
        stop()
      }
    }

    eventSource.value.onerror = () => {
      error.value = 'RAG 问答连接已断开'
      stop()
    }
  }

  const clear = () => {
    stop()
    messages.value = []
    error.value = null
  }

  return {
    messages,
    isAnswering,
    error,
    ask,
    clear,
    stop,
  }
}
