<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { chatApi, createChatWebSocket, type Message, type Conversation, type ReportPreview } from '@/api/chat'
import AgentBubble from '@/components/AgentBubble.vue'
import ReportPreviewCard from '@/components/ReportPreviewCard.vue'

const route = useRoute()
const router = useRouter()

const conversationId = computed(() => route.params.conversationId as string)

// 状态
const conversations = ref<Conversation[]>([])
const currentConversation = ref<Conversation | null>(null)
const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const isSending = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

// WebSocket
let ws: WebSocket | null = null

// 加载会话列表
async function loadConversations() {
  try {
    const { conversations: list } = await chatApi.getConversations()
    conversations.value = list
  } catch (e) {
    console.error('加载会话列表失败:', e)
  }
}

// 加载当前会话
async function loadConversation() {
  if (!conversationId.value) return
  
  isLoading.value = true
  try {
    const { conversation, messages: msgList } = await chatApi.getConversation(conversationId.value)
    currentConversation.value = conversation
    messages.value = msgList
    
    // 连接 WebSocket
    connectWebSocket()
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('加载会话失败:', e)
    ElMessage.error('会话不存在或加载失败')
    router.push('/')
  } finally {
    isLoading.value = false
  }
}

// 连接 WebSocket
function connectWebSocket() {
  if (ws) {
    ws.close()
  }
  
  ws = createChatWebSocket(
    conversationId.value,
    handleWebSocketMessage,
    () => ElMessage.warning('连接中断，请刷新页面'),
    () => console.log('WebSocket 已关闭')
  )
}

// 处理 WebSocket 消息
function handleWebSocketMessage(data: any) {
  console.log('收到 WebSocket 消息:', data)
  
  if (data.message) {
    // 添加新消息
    messages.value.push(data.message)
    
    // 更新会话列表
    if (data.type === 'report_complete') {
      loadConversations()
    }
    
    // 滚动到底部
    nextTick(() => scrollToBottom())
  }
}

// 发送消息
async function handleSend() {
  if (!inputMessage.value.trim() || isSending.value) return
  
  const message = inputMessage.value.trim()
  inputMessage.value = ''
  isSending.value = true
  
  try {
    // 立即添加用户消息到界面（乐观更新）
    messages.value.push({
      id: `temp-${Date.now()}`,
      conversation_id: conversationId.value,
      role: 'user',
      message_type: 'text',
      content: message,
      agent_name: null,
      agent_status: null,
      extra_data: null,
      created_at: new Date().toISOString()
    })
    
    await nextTick()
    scrollToBottom()
    
    // 发送到后端
    const result = await chatApi.sendMessage(conversationId.value, message)
    
    // 如果意图解析返回了消息，添加助手回复
    if (result.intent?.message && !result.success) {
      messages.value.push({
        id: `temp-${Date.now() + 1}`,
        conversation_id: conversationId.value,
        role: 'assistant',
        message_type: 'text',
        content: result.intent.message,
        agent_name: null,
        agent_status: null,
        extra_data: null,
        created_at: new Date().toISOString()
      })
    }
    
    // 刷新会话列表
    loadConversations()
    
  } catch (e) {
    console.error('发送消息失败:', e)
    ElMessage.error('发送失败，请重试')
    // 恢复输入
    inputMessage.value = message
  } finally {
    isSending.value = false
    await nextTick()
    scrollToBottom()
  }
}

// 处理回车
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 滚动到底部
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 创建新会话
async function createNewConversation() {
  try {
    const { conversation_id } = await chatApi.createConversation()
    router.push({ name: 'Chat', params: { conversationId: conversation_id } })
  } catch (e) {
    ElMessage.error('创建会话失败')
  }
}

// 切换会话
function switchConversation(id: string) {
  if (id !== conversationId.value) {
    router.push({ name: 'Chat', params: { conversationId: id } })
  }
}

// 格式化时间
function formatTime(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 处理初始消息
async function handleInitialMessage() {
  const initialMessage = route.query.initialMessage as string
  if (initialMessage && messages.value.length === 0) {
    inputMessage.value = initialMessage
    // 清除 query 参数
    router.replace({ params: route.params })
    // 自动发送
    await nextTick()
    handleSend()
  }
}

// 监听路由变化
watch(conversationId, (newId) => {
  if (newId) {
    loadConversation()
  }
})

onMounted(async () => {
  await loadConversations()
  await loadConversation()
  handleInitialMessage()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<template>
  <div class="chat-view">
    <!-- 左侧会话列表 -->
    <aside class="conversation-sidebar">
      <div class="sidebar-header">
        <h3>对话历史</h3>
        <el-button type="primary" size="small" @click="createNewConversation">
          <el-icon><Plus /></el-icon>
          新对话
        </el-button>
      </div>
      
      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          :class="['conversation-item', { active: conv.id === conversationId }]"
          @click="switchConversation(conv.id)"
        >
          <div class="conv-icon">
            <el-icon v-if="conv.status === 'completed'"><CircleCheck /></el-icon>
            <el-icon v-else-if="conv.status === 'active'"><Loading /></el-icon>
            <el-icon v-else><ChatDotRound /></el-icon>
          </div>
          <div class="conv-info">
            <span class="conv-title">{{ conv.title || '新对话' }}</span>
            <span class="conv-date">{{ formatTime(conv.updated_at) }}</span>
          </div>
        </div>
        
        <el-empty v-if="conversations.length === 0" description="暂无对话" :image-size="60" />
      </div>
      
      <!-- 返回首页 -->
      <div class="sidebar-footer">
        <router-link to="/" class="back-home">
          <el-icon><HomeFilled /></el-icon>
          返回首页
        </router-link>
      </div>
    </aside>
    
    <!-- 右侧聊天区域 -->
    <main class="chat-main">
      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-overlay">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      
      <!-- 聊天内容 -->
      <div v-else class="chat-content">
        <!-- 消息列表 -->
        <div ref="messagesContainer" class="messages-container">
          <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="welcome-message">
            <div class="welcome-icon">🤖</div>
            <h3>欢迎使用 AI 研究助手</h3>
            <p>请输入您想研究的公司名称，我会为您生成专业的研究报告。</p>
            <div class="example-prompts">
              <span 
                v-for="prompt in ['帮我分析一下贵州茅台', '生成腾讯的研究报告', '我想了解比亚迪']"
                :key="prompt"
                class="example-prompt"
                @click="inputMessage = prompt"
              >
                {{ prompt }}
              </span>
            </div>
          </div>
          
          <!-- 消息列表 -->
          <template v-for="msg in messages" :key="msg.id">
            <!-- 用户消息 -->
            <div v-if="msg.role === 'user'" class="message-wrapper user">
              <div class="message-bubble user-bubble">
                {{ msg.content }}
              </div>
            </div>
            
            <!-- 助手消息 -->
            <div v-else-if="msg.role === 'assistant'" class="message-wrapper assistant">
              <!-- 报告预览 -->
              <ReportPreviewCard 
                v-if="msg.message_type === 'report_preview' && msg.extra_data"
                :preview="(msg.extra_data as ReportPreview)"
              />
              <!-- 普通消息 -->
              <div v-else class="message-bubble assistant-bubble">
                <div class="assistant-avatar">🤖</div>
                <div class="message-content">{{ msg.content }}</div>
              </div>
            </div>
            
            <!-- Agent 状态消息 -->
            <div v-else-if="msg.role === 'agent'" class="message-wrapper agent">
              <AgentBubble 
                :agent-name="msg.agent_name || ''"
                :status="msg.agent_status || 'working'"
                :content="msg.content"
                :message-type="msg.message_type"
                :extra-data="msg.extra_data"
              />
            </div>
          </template>
          
          <!-- 正在输入指示器 -->
          <div v-if="isSending" class="message-wrapper assistant">
            <div class="message-bubble assistant-bubble typing">
              <div class="assistant-avatar">🤖</div>
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-container">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 4 }"
              placeholder="输入消息..."
              :disabled="isSending"
              @keydown="handleKeydown"
            />
            <el-button
              type="primary"
              :loading="isSending"
              :disabled="!inputMessage.trim()"
              class="send-btn"
              @click="handleSend"
            >
              <el-icon v-if="!isSending"><Promotion /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  height: calc(100vh - 64px);
  background: var(--bg-color);
}

/* 左侧会话列表 */
.conversation-sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.conversation-item:hover {
  background: var(--bg-color);
}

.conversation-item.active {
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.1) 0%, rgba(15, 52, 96, 0.1) 100%);
}

.conv-icon {
  width: 36px;
  height: 36px;
  background: var(--bg-color);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  display: block;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-date {
  font-size: 12px;
  color: var(--text-light);
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}

.back-home {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-light);
  text-decoration: none;
  font-size: 14px;
}

.back-home:hover {
  color: var(--primary-color);
}

/* 右侧聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.loading-overlay {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-light);
}

.loading-icon {
  font-size: 32px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 消息列表 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome-message h3 {
  font-size: 24px;
  margin-bottom: 8px;
}

.welcome-message p {
  color: var(--text-light);
  margin-bottom: 24px;
}

.example-prompts {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.example-prompt {
  padding: 8px 16px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.example-prompt:hover {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

/* 消息气泡 */
.message-wrapper {
  margin-bottom: 16px;
}

.message-wrapper.user {
  display: flex;
  justify-content: flex-end;
}

.message-wrapper.assistant,
.message-wrapper.agent {
  display: flex;
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.5;
}

.user-bubble {
  background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.assistant-bubble {
  background: white;
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 4px;
  display: flex;
  gap: 12px;
}

.assistant-avatar {
  font-size: 24px;
  flex-shrink: 0;
}

.message-content {
  white-space: pre-wrap;
}

/* 输入指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--text-light);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 输入区域 */
.input-area {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
  background: white;
}

.input-container {
  display: flex;
  gap: 12px;
  max-width: 800px;
  margin: 0 auto;
}

.input-container :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 15px;
  resize: none;
}

.send-btn {
  width: 48px;
  height: 48px;
  border-radius: 12px;
}

/* 响应式 */
@media (max-width: 768px) {
  .conversation-sidebar {
    display: none;
  }
}
</style>

