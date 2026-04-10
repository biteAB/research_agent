import { ref } from 'vue'

export type TaskStatus = 'pending' | 'planning' | 'searching' | 'summarizing' | 'reporting' | 'done' | 'error'

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
  // Track individual task status for parallel execution
  const taskStatusMap = ref<Map<string, TaskStatus>>(new Map())
  // Track expanded task for detail panel
  const expandedTaskId = ref<string | null>(null)
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
      taskStatusMap.value.clear()
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

    eventSource.value.onerror = (event) => {
      console.error('SSE error:', event)
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
        // Initialize all tasks as pending
        taskStatusMap.value.clear()
        event.data.todos.forEach((task: TodoTask) => {
          taskStatusMap.value.set(task.id, 'pending')
        })
        currentStatus.value = 'searching'
        break

      case 'searching':
        const searchingTaskId = event.data.task_id
        taskStatusMap.value.set(searchingTaskId, 'searching')
        currentTaskId.value = searchingTaskId
        currentTaskTitle.value = event.data.task_title
        currentStatus.value = 'searching'
        break

      case 'summarizing':
        const summarizingTaskId = event.data.task_id
        taskStatusMap.value.set(summarizingTaskId, 'summarizing')
        currentTaskId.value = summarizingTaskId
        currentTaskTitle.value = event.data.task_title
        currentStatus.value = 'summarizing'
        break

      case 'summary_done':
        summaries.value.push(event.data)
        taskStatusMap.value.set(event.data.task_id, 'done')
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
    return taskStatusMap.value.get(taskId) || 'pending'
  }

  const toggleTaskExpand = (taskId: string) => {
    if (expandedTaskId.value === taskId) {
      expandedTaskId.value = null
    } else {
      expandedTaskId.value = taskId
    }
  }

  const getTaskSummary = (taskId: string): TaskSummary | undefined => {
    return summaries.value.find(s => s.task_id === taskId)
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
    taskStatusMap.value.clear()
    expandedTaskId.value = null
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
    expandedTaskId,
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
    getTaskSummary,
    toggleTaskExpand,
  }
}

export type UseResearchReturn = ReturnType<typeof useResearch>
