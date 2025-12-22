<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useResearchStore } from '@/stores/research'
import CompanyInput from '@/components/CompanyInput.vue'

const router = useRouter()
const store = useResearchStore()

const isStarting = ref(false)

onMounted(() => {
  store.fetchHistory()
})

async function handleStartResearch(data: { company: string; depth: string; focus: string[] }) {
  isStarting.value = true
  try {
    const taskId = await store.startResearch(data.company, data.depth, data.focus)
    ElMessage.success('研究任务已启动')
    router.push(`/research/${taskId}`)
  } catch {
    ElMessage.error('启动研究失败，请重试')
  } finally {
    isStarting.value = false
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getStatusType(status: string) {
  const types: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    pending: '等待中',
    running: '研究中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

function viewTask(task: { id: string; status: string }) {
  if (task.status === 'completed') {
    router.push(`/research/${task.id}`)
  } else {
    router.push(`/research/${task.id}`)
  }
}
</script>

<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="gradient-text">AI 驱动</span>
          <br />
          上市公司深度研究
        </h1>
        <p class="hero-subtitle">
          基于多 Agent 协同的智能研究系统，自动收集数据、分析财务、评估市场，生成专业研究报告
        </p>
        <div class="hero-features">
          <div class="feature-item">
            <el-icon :size="20"><Search /></el-icon>
            <span>智能数据收集</span>
          </div>
          <div class="feature-item">
            <el-icon :size="20"><DataLine /></el-icon>
            <span>财务深度分析</span>
          </div>
          <div class="feature-item">
            <el-icon :size="20"><Document /></el-icon>
            <span>专业报告生成</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Research Input Section -->
    <section class="input-section">
      <el-card class="input-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon :size="24"><Search /></el-icon>
            <span>开始研究</span>
          </div>
        </template>
        <CompanyInput 
          @start="handleStartResearch" 
          :loading="isStarting"
        />
      </el-card>
    </section>

    <!-- History Section -->
    <section class="history-section" v-if="store.historyTasks.length > 0">
      <h2 class="section-title">
        <el-icon :size="22"><Clock /></el-icon>
        研究历史
      </h2>
      <div class="history-grid">
        <el-card 
          v-for="task in store.historyTasks" 
          :key="task.id"
          class="history-card"
          shadow="hover"
          @click="viewTask(task)"
        >
          <div class="task-header">
            <span class="company-name">{{ task.company }}</span>
            <el-tag :type="getStatusType(task.status)" size="small">
              {{ getStatusText(task.status) }}
            </el-tag>
          </div>
          <div class="task-info">
            <div class="info-item">
              <span class="label">研究深度:</span>
              <span class="value">{{ task.depth === 'deep' ? '深度' : task.depth === 'basic' ? '基础' : '标准' }}</span>
            </div>
            <div class="info-item">
              <span class="label">创建时间:</span>
              <span class="value">{{ formatDate(task.created_at) }}</span>
            </div>
          </div>
          <div class="task-progress" v-if="task.status === 'running'">
            <el-progress :percentage="task.progress" :stroke-width="6" />
          </div>
        </el-card>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

.hero-section {
  text-align: center;
  padding: 60px 20px 40px;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 20px;
  color: var(--primary-color);
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
  max-width: 600px;
  margin: 0 auto 32px;
  line-height: 1.6;
}

.hero-features {
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--accent-color);
  font-size: 15px;
}

.input-section {
  padding: 0 20px 40px;
}

.input-card {
  max-width: 700px;
  margin: 0 auto;
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-color);
}

.history-section {
  padding: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--primary-color);
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.history-card {
  cursor: pointer;
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.history-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.company-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-color);
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.info-item .label {
  color: var(--text-light);
}

.info-item .value {
  color: var(--text-color);
}

.task-progress {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }
  
  .hero-features {
    gap: 20px;
  }
  
  .history-grid {
    grid-template-columns: 1fr;
  }
}
</style>






