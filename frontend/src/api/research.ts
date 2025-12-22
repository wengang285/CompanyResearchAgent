import type { ResearchRequest, ResearchTask, Report } from '@/types'
import { createAuthenticatedApi } from './auth'

const api = createAuthenticatedApi('/api')

// 研究相关 API
export const researchApi = {
  // 启动研究任务
  async startResearch(request: ResearchRequest): Promise<{ task_id: string; message: string }> {
    const response = await api.post('/research/start', request)
    return response.data
  },

  // 获取任务状态
  async getTaskStatus(taskId: string): Promise<ResearchTask> {
    const response = await api.get(`/research/${taskId}/status`)
    return response.data
  },

  // 获取研究结果
  async getTaskResult(taskId: string): Promise<{ task_id: string; company: string; status: string; report: Report }> {
    const response = await api.get(`/research/${taskId}/result`)
    return response.data
  },

  // 获取历史记录
  async getHistory(limit: number = 20): Promise<{ tasks: ResearchTask[] }> {
    const response = await api.get('/research/history', { params: { limit } })
    return response.data
  },

  // 创建 WebSocket 连接
  createProgressWebSocket(taskId: string): WebSocket {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return new WebSocket(`${protocol}//${host}/api/research/${taskId}/progress`)
  }
}

// 报告相关 API
export const reportApi = {
  // 获取报告列表
  async listReports(limit: number = 20): Promise<{ reports: Report[] }> {
    const response = await api.get('/reports', { params: { limit } })
    return response.data
  },

  // 获取报告详情
  async getReport(reportId: string): Promise<Report> {
    const response = await api.get(`/reports/${reportId}`)
    return response.data
  },

  // 下载 PDF
  async downloadPdf(reportId: string): Promise<Blob> {
    const response = await api.get(`/reports/${reportId}/pdf`, {
      responseType: 'blob'
    })
    return response.data
  },

  // 从任务生成报告
  async generateFromTask(taskId: string): Promise<{ report_id: string; message: string }> {
    const response = await api.post(`/reports/${taskId}/generate`)
    return response.data
  }
}



