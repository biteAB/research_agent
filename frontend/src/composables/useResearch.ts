import { ref } from 'vue'

export type TaskStatus = 'pending' | 'planning' | 'searching' | 'summarizing' | 'done' | 'error'

export interface TodoTask {
  id: string
  title: string
  intent: string
  search_queries: string[]
}

export interface TaskSummary {
  task_id: string
  summary: string
  key_points: string[]
  sources: string[]
}

export interface SSEEvent {
  event: string
  data: any
}

export function useResearch() {
  const taskId = ref<string | null>(null)
  const isRunning = ref(false)
  const currentStatus = ref<TaskStatus>('pending')
  const currentTaskId = ref<string | null>(null)
  const currentTaskTitle = ref<string>('')
  const todos = ref<TodoTask[]>([])
  const summaries = ref<TaskSummary[]>([])
  const report = ref('')
  const error = ref<string | null>(null)
  const eventSource = ref<EventSource | null>(null)

  const startResearch = async (topic: string): Promise<string | null> => {
    try {
      const response = await fetch('/api/research/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic }),
      })

      const data = await response.json()
      const newTaskId = data.task_id
      taskId.value = newTaskId

      // Reset state
      isRunning.value = true
      currentStatus.value = 'pending'
      currentTaskId.value = null
      currentTaskTitle.value = ''
      todos.value = []
      summaries.value = []
      report.value = ''
      error.value = null

      // Connect SSE
      connectSSE(newTaskId)

      return newTaskId
    } catch (e) {
      error.value = e instanceof Error ? e.message : '启动研究失败'
      return null
    }
  }

  const connectSSE = (id: string) => {
    eventSource.value = new EventSource(`/api/research/stream/${id}`)

    eventSource.value.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as SSEEvent
        handleEvent(parsed)
      } catch (e) {
        console.error('Failed to parse SSE event:', e)
      }
    }

    eventSource.value.onerror = (error) => {
      console.error('SSE error:', error)
      stopResearch()
      if (!error.value) {
        error.value = '连接断开'
      }
    }
  }

  const handleEvent = (event: SSEEvent) => {
    switch (event.event) {
      case 'status':
        currentStatus.value = event.data.message.includes('计划') ? 'planning' : currentStatus.value
        break

      case 'planning':
        todos.value = event.data.todos
        currentStatus.value = 'searching'
        break

      case 'searching':
        currentTaskId.value = event.data.task_id
        currentTaskTitle.value = event.data.task_title
        currentStatus.value = 'searching'
        break

      case 'summarizing':
        currentTaskId.value = event.data.task_id
        currentTaskTitle.value = event.data.task_title
        currentStatus.value = 'summarizing'
        break

      case 'summary_done':
        summaries.value.push(event.data)
        break

      case 'reporting':
        currentStatus.value = 'reporting'
        break

      case 'report_chunk':
        report.value += event.data.chunk
        break

      case 'done':
        report.value = event.data.report
        currentStatus.value = 'done'
        isRunning.value = false
        stopResearch()
        break

      case 'error':
        error.value = event.data.message
        currentStatus.value = 'error'
        isRunning.value = false
        stopResearch()
        break

      default:
        console.log('Unknown event:', event.event)
    }
  }

  const getTaskStatus = (taskId: string): TaskStatus => {
    if (summaries.value.some(s => s.task_id === taskId)) {
      return 'done'
    }
    if (currentTaskId.value === taskId) {
      return currentStatus.value === 'searching' ? 'searching' : 'summarizing'
    }
    return 'pending'
  }

  const stopResearch = () => {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    isRunning.value = false
  }

  const reset = () => {
    stopResearch()
    taskId.value = null
    isRunning.value = false
    currentStatus.value = 'pending'
    currentTaskId.value = null
    currentTaskTitle.value = ''
    todos.value = []
    summaries.value = []
    report.value = ''
    error.value = null
  }

  return {
    taskId,
    isRunning,
    currentStatus,
    currentTaskId,
    currentTaskTitle,
    todos,
    summaries,
    report,
    error,
    startResearch,
    stopResearch,
    reset,
    getTaskStatus,
  }
}

export type UseResearchReturn = ReturnType<typeof useResearch>
