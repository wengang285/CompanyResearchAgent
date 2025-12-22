import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ResearchTask, ResearchProgress, Report } from '@/types'
import { researchApi, reportApi } from '@/api/research'

export const useResearchStore = defineStore('research', () => {
  // 状态
  const currentTask = ref<ResearchTask | null>(null)
  const progress = ref<ResearchProgress>({
    status: 'pending',
    progress: 0,
    currentAgent: '',
    currentTask: '',
    estimatedTime: 0
  })
  const historyTasks = ref<ResearchTask[]>([])
  const reports = ref<Report[]>([])
  const wsConnection = ref<WebSocket | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  
  // 轮询定时器
  let pollingTimer: ReturnType<typeof setInterval> | null = null
  let wsRetryCount = 0
  const MAX_WS_RETRIES = 3

  // 计算属性
  const isResearching = computed(() => 
    currentTask.value?.status === 'running' || currentTask.value?.status === 'pending'
  )

  // 操作
  async function startResearch(company: string, depth: string = 'standard', focus: string[] = []) {
    isLoading.value = true
    error.value = null
    
    try {
      const result = await researchApi.startResearch({
        company,
        depth: depth as 'basic' | 'standard' | 'deep',
        focus
      })
      
      // 立即获取任务状态
      const task = await researchApi.getTaskStatus(result.task_id)
      currentTask.value = task
      
      // 重置进度
      resetProgress()
      progress.value.status = task.status as ResearchProgress['status']
      
      // 开始状态同步（WebSocket + 轮询后备）
      startStatusSync(result.task_id)
      
      return result.task_id
    } catch (e: unknown) {
      const err = e as Error
      error.value = err.message || '启动研究失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  // 开始状态同步
  function startStatusSync(taskId: string) {
    // 尝试 WebSocket 连接
    wsRetryCount = 0
    connectWebSocket(taskId)
    
    // 同时启动轮询作为后备
    startPolling(taskId)
  }

  // 停止状态同步
  function stopStatusSync() {
    if (wsConnection.value) {
      wsConnection.value.close()
      wsConnection.value = null
    }
    stopPolling()
  }

  // 轮询获取状态
  function startPolling(taskId: string) {
    stopPolling()
    
    pollingTimer = setInterval(async () => {
      try {
        const task = await researchApi.getTaskStatus(taskId)
        updateFromTask(task)
        
        // 如果任务完成或失败，停止轮询
        if (task.status === 'completed' || task.status === 'failed') {
          stopStatusSync()
        }
      } catch (e) {
        console.error('轮询状态失败:', e)
      }
    }, 2000) // 每2秒轮询一次
  }

  function stopPolling() {
    if (pollingTimer) {
      clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  // 从任务更新状态
  function updateFromTask(task: ResearchTask) {
    currentTask.value = task
    progress.value = {
      status: task.status as ResearchProgress['status'],
      progress: task.progress,
      currentAgent: task.current_agent || '',
      currentTask: task.current_task || '',
      estimatedTime: task.estimated_time || 0
    }
  }

  function connectWebSocket(taskId: string) {
    // 关闭旧连接
    if (wsConnection.value) {
      wsConnection.value.close()
    }

    try {
      const ws = researchApi.createProgressWebSocket(taskId)
      
      ws.onopen = () => {
        console.log('[WS] 已连接')
        wsRetryCount = 0
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'heartbeat') {
            return
          }

          console.log('[WS] 收到消息:', data)

          progress.value = {
            status: data.status,
            progress: data.progress,
            currentAgent: data.currentAgent || '',
            currentTask: data.currentTask || '',
            estimatedTime: data.estimatedTime || 0
          }

          // 更新当前任务状态
          if (currentTask.value) {
            currentTask.value.status = data.status
            currentTask.value.progress = data.progress
            currentTask.value.current_agent = data.currentAgent
            currentTask.value.current_task = data.currentTask
          }

          // 如果完成或失败，停止同步
          if (data.status === 'completed' || data.status === 'failed') {
            stopStatusSync()
          }
        } catch (e) {
          console.error('[WS] 解析消息失败:', e)
        }
      }

      ws.onerror = (e) => {
        console.error('[WS] 错误:', e)
      }

      ws.onclose = () => {
        console.log('[WS] 已关闭')
        wsConnection.value = null
        
        // 尝试重连
        if (wsRetryCount < MAX_WS_RETRIES && isResearching.value) {
          wsRetryCount++
          console.log(`[WS] 尝试重连 (${wsRetryCount}/${MAX_WS_RETRIES})...`)
          setTimeout(() => {
            if (currentTask.value && isResearching.value) {
              connectWebSocket(currentTask.value.id)
            }
          }, 2000)
        }
      }

      wsConnection.value = ws
    } catch (e) {
      console.error('[WS] 创建连接失败:', e)
    }
  }

  async function fetchTaskStatus(taskId: string) {
    try {
      const task = await researchApi.getTaskStatus(taskId)
      updateFromTask(task)
      return task
    } catch (e: unknown) {
      const err = e as Error
      error.value = err.message
      throw e
    }
  }

  async function fetchTaskResult(taskId: string) {
    try {
      const result = await researchApi.getTaskResult(taskId)
      if (currentTask.value && currentTask.value.id === taskId) {
        currentTask.value.report_data = result.report
      }
      return result.report
    } catch (e: unknown) {
      const err = e as Error
      error.value = err.message
      throw e
    }
  }

  async function fetchHistory() {
    try {
      const result = await researchApi.getHistory()
      historyTasks.value = result.tasks
    } catch (e: unknown) {
      const err = e as Error
      error.value = err.message
    }
  }

  async function fetchReports() {
    try {
      const result = await reportApi.listReports()
      reports.value = result.reports
    } catch (e: unknown) {
      const err = e as Error
      error.value = err.message
    }
  }

  function resetProgress() {
    progress.value = {
      status: 'pending',
      progress: 0,
      currentAgent: '',
      currentTask: '',
      estimatedTime: 0
    }
  }

  function cleanup() {
    stopStatusSync()
    currentTask.value = null
    resetProgress()
  }

  return {
    // 状态
    currentTask,
    progress,
    historyTasks,
    reports,
    isLoading,
    error,
    // 计算属性
    isResearching,
    // 操作
    startResearch,
    fetchTaskStatus,
    fetchTaskResult,
    fetchHistory,
    fetchReports,
    connectWebSocket,
    startStatusSync,
    stopStatusSync,
    resetProgress,
    cleanup
  }
})
