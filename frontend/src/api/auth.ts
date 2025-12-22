/**
 * 认证 API
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/auth',
  timeout: 30000
})

export interface User {
  id: string
  username: string
  email: string | null
  is_admin: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

// Token 管理
const TOKEN_KEY = 'auth_token'
const USER_KEY = 'auth_user'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getStoredUser(): User | null {
  const userStr = localStorage.getItem(USER_KEY)
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  }
  return null
}

export function setStoredUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function isAuthenticated(): boolean {
  return !!getToken()
}

// API 请求拦截器 - 添加 token
api.interceptors.request.use(config => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authApi = {
  /**
   * 用户注册
   */
  async register(username: string, password: string, email?: string): Promise<LoginResponse> {
    const response = await api.post('/register', { username, password, email })
    const data = response.data
    setToken(data.access_token)
    setStoredUser(data.user)
    return data
  },

  /**
   * 用户登录
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    // OAuth2 表单格式
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await api.post('/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    const data = response.data
    setToken(data.access_token)
    setStoredUser(data.user)
    return data
  },

  /**
   * 获取当前用户
   */
  async getMe(): Promise<User> {
    const response = await api.get('/me')
    return response.data
  },

  /**
   * 登出
   */
  async logout(): Promise<void> {
    try {
      await api.post('/logout')
    } finally {
      removeToken()
    }
  }
}

// 为其他 API 模块提供带认证的 axios 实例
export function createAuthenticatedApi(baseURL: string) {
  const instance = axios.create({
    baseURL,
    timeout: 60000
  })
  
  instance.interceptors.request.use(config => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })
  
  // 401 响应拦截 - 跳转登录
  instance.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        removeToken()
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )
  
  return instance
}




