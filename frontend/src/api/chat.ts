/**
 * 聊天 API
 */
import { createAuthenticatedApi } from './auth'

const api = createAuthenticatedApi('/api/chat')

export interface Conversation {
  id: string
  title: string
  company: string | null
  status: string
  task_id: string | null
  created_at: string
  updated_at: string
  message_count: number
}

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant' | 'agent' | 'system'
  message_type: 'text' | 'agent_status' | 'agent_result' | 'report_preview' | 'error' | 'streaming'
  content: string
  agent_name: string | null
  agent_status: string | null
  extra_data: Record<string, any> | null
  created_at: string
}

export interface ReportPreview {
  task_id: string
  company: string
  company_name: string
  overall_score: number
  recommendation: string
  executive_summary: string
  report_url: string
}

export interface HistoryReport {
  task_id: string
  company: string
  company_name: string
  overall_score: number
  recommendation: string
  completed_at: string
}

export const chatApi = {
  /**
   * 创建新会话
   */
  async createConversation(): Promise<{ conversation_id: string }> {
    const response = await api.post('/conversations')
    return response.data
  },

  /**
   * 获取会话列表
   */
  async getConversations(limit = 50): Promise<{ conversations: Conversation[] }> {
    const response = await api.get('/conversations', { params: { limit } })
    return response.data
  },

  /**
   * 获取会话详情和消息
   */
  async getConversation(conversationId: string): Promise<{
    conversation: Conversation
    messages: Message[]
  }> {
    const response = await api.get(`/conversations/${conversationId}`)
    return response.data
  },

  /**
   * 发送消息
   */
  async sendMessage(conversationId: string, message: string): Promise<{
    success: boolean
    intent: {
      intent_type: string
      company: string | null
      confidence: number
      message: string
    }
    task_id: string | null
  }> {
    const response = await api.post(`/conversations/${conversationId}/messages`, {
      message
    })
    return response.data
  },

  /**
   * 获取历史研究报告
   */
  async getHistoryReports(limit = 20): Promise<{ reports: HistoryReport[] }> {
    const response = await api.get('/history/reports', { params: { limit } })
    return response.data
  }
}

/**
 * 创建 WebSocket 连接
 */
export function createChatWebSocket(
  conversationId: string,
  onMessage: (data: any) => void,
  onError?: (error: Event) => void,
  onClose?: () => void
): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const ws = new WebSocket(`${protocol}//${host}/api/chat/conversations/${conversationId}/ws`)
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage(data)
    } catch (e) {
      console.error('WebSocket 消息解析失败:', e)
    }
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error)
    onError?.(error)
  }
  
  ws.onclose = () => {
    console.log('WebSocket 连接关闭')
    onClose?.()
  }
  
  return ws
}

