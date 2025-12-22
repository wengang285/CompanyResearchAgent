<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { chatApi, type HistoryReport } from '@/api/chat'

const router = useRouter()
const inputMessage = ref('')
const isLoading = ref(false)
const historyReports = ref<HistoryReport[]>([])
const isLoadingHistory = ref(true)

// 加载历史报告
onMounted(async () => {
  try {
    const { reports } = await chatApi.getHistoryReports(12)
    historyReports.value = reports
  } catch (e) {
    console.error('获取历史报告失败:', e)
  } finally {
    isLoadingHistory.value = false
  }
})

// 发送消息
async function handleSend() {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  isLoading.value = true
  try {
    // 创建新会话
    const { conversation_id } = await chatApi.createConversation()
    
    // 跳转到聊天页面，带上初始消息
    router.push({
      name: 'Chat',
      params: { conversationId: conversation_id },
      query: { initialMessage: inputMessage.value }
    })
  } catch (e) {
    console.error('创建会话失败:', e)
    ElMessage.error('创建会话失败，请重试')
    isLoading.value = false
  }
}

// 处理回车
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 跳转到报告详情
function goToReport(taskId: string) {
  window.open(`/report/${taskId}`, '_blank')
}

// 获取评级样式
function getRecommendationClass(recommendation: string) {
  const map: Record<string, string> = {
    '买入': 'buy',
    '持有': 'hold',
    '卖出': 'sell',
    '观望': 'watch'
  }
  return map[recommendation] || 'watch'
}

// 获取评分颜色
function getScoreColor(score: number) {
  if (score >= 8) return '#10b981'
  if (score >= 6) return '#f59e0b'
  return '#ef4444'
}

// 格式化日期
function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric'
  })
}
</script>

<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="gradient-text">AI 驱动的</span>
          <br />
          上市公司深度研究
        </h1>
        <p class="hero-subtitle">
          输入公司名称，多个 AI Agent 协作为您生成专业研究报告
        </p>
        
        <!-- 聊天输入框 -->
        <div class="chat-input-wrapper">
          <div class="chat-input-container">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 4 }"
              placeholder="输入您想研究的公司，例如：帮我分析一下贵州茅台..."
              class="chat-input"
              @keydown="handleKeydown"
            />
            <el-button
              type="primary"
              :loading="isLoading"
              :disabled="!inputMessage.trim()"
              class="send-button"
              @click="handleSend"
            >
              <el-icon v-if="!isLoading"><Promotion /></el-icon>
              <span>{{ isLoading ? '创建中...' : '开始研究' }}</span>
            </el-button>
          </div>
          <div class="input-tips">
            <span class="tip-item">💡 支持公司名称或股票代码</span>
            <span class="tip-item">📊 自动生成专业研究报告</span>
            <span class="tip-item">⚡ 多 Agent 并行分析</span>
          </div>
        </div>
      </div>
      
      <!-- 装饰元素 -->
      <div class="hero-decoration">
        <div class="decoration-circle circle-1"></div>
        <div class="decoration-circle circle-2"></div>
        <div class="decoration-circle circle-3"></div>
      </div>
    </section>

    <!-- 历史报告 -->
    <section v-if="historyReports.length > 0" class="history-section">
      <div class="section-header">
        <h2 class="section-title">
          <el-icon><Document /></el-icon>
          历史研究报告
        </h2>
        <router-link to="/history" class="view-all">
          查看全部
          <el-icon><ArrowRight /></el-icon>
        </router-link>
      </div>
      
      <div class="report-grid">
        <div
          v-for="report in historyReports"
          :key="report.task_id"
          class="report-card"
          @click="goToReport(report.task_id)"
        >
          <div class="card-header">
            <span class="company-name">{{ report.company_name || report.company }}</span>
            <span 
              class="recommendation-tag"
              :class="getRecommendationClass(report.recommendation)"
            >
              {{ report.recommendation }}
            </span>
          </div>
          <div class="card-body">
            <div class="score-display">
              <span class="score-value" :style="{ color: getScoreColor(report.overall_score) }">
                {{ report.overall_score }}
              </span>
              <span class="score-max">/10</span>
            </div>
            <span class="score-label">综合评分</span>
          </div>
          <div class="card-footer">
            <span class="date">{{ formatDate(report.completed_at) }}</span>
            <el-icon class="arrow-icon"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </section>

    <!-- 空状态 -->
    <section v-else-if="!isLoadingHistory" class="empty-section">
      <div class="empty-content">
        <el-icon :size="64" color="#d1d5db"><DocumentRemove /></el-icon>
        <p>还没有研究报告，开始您的第一次研究吧！</p>
      </div>
    </section>

    <!-- 加载状态 -->
    <section v-else class="loading-section">
      <el-skeleton :rows="3" animated />
    </section>
  </div>
</template>

<style scoped>
.home-page {
  min-height: calc(100vh - 64px);
  padding: 40px 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* Hero Section */
.hero-section {
  position: relative;
  text-align: center;
  padding: 60px 0 80px;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 48px;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 20px;
  color: var(--text-color);
}

.gradient-text {
  background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 18px;
  color: var(--text-light);
  margin-bottom: 40px;
}

/* 聊天输入框 */
.chat-input-wrapper {
  max-width: 700px;
  margin: 0 auto;
}

.chat-input-container {
  display: flex;
  gap: 12px;
  background: white;
  padding: 12px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-color);
}

.chat-input {
  flex: 1;
}

.chat-input :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding: 12px 16px;
  font-size: 16px;
  resize: none;
}

.chat-input :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.send-button {
  height: auto;
  min-height: 48px;
  padding: 0 24px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
}

.send-button .el-icon {
  margin-right: 8px;
}

.input-tips {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
}

.tip-item {
  font-size: 14px;
  color: var(--text-light);
}

/* 装饰元素 */
.hero-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
}

.circle-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
  top: -100px;
  right: -100px;
}

.circle-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #0f3460 0%, #e94560 100%);
  bottom: -50px;
  left: -50px;
}

.circle-3 {
  width: 200px;
  height: 200px;
  background: #e94560;
  top: 50%;
  left: 10%;
}

/* 历史报告 */
.history-section {
  margin-top: 60px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color);
}

.view-all {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--primary-color);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}

.view-all:hover {
  text-decoration: underline;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.report-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
}

.report-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.company-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
}

.recommendation-tag {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.recommendation-tag.buy {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.recommendation-tag.hold {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.recommendation-tag.sell {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.recommendation-tag.watch {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.card-body {
  text-align: center;
  padding: 16px 0;
}

.score-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
}

.score-value {
  font-size: 48px;
  font-weight: 700;
}

.score-max {
  font-size: 20px;
  color: var(--text-light);
  margin-left: 4px;
}

.score-label {
  font-size: 14px;
  color: var(--text-light);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.date {
  font-size: 13px;
  color: var(--text-light);
}

.arrow-icon {
  color: var(--text-light);
}

/* 空状态 */
.empty-section {
  margin-top: 60px;
  text-align: center;
  padding: 60px 0;
}

.empty-content {
  color: var(--text-light);
}

.empty-content p {
  margin-top: 16px;
  font-size: 16px;
}

/* 加载状态 */
.loading-section {
  margin-top: 60px;
  padding: 40px;
  background: white;
  border-radius: 16px;
}

/* 响应式 */
@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }
  
  .chat-input-container {
    flex-direction: column;
  }
  
  .send-button {
    width: 100%;
  }
  
  .input-tips {
    flex-direction: column;
    gap: 8px;
  }
}
</style>

