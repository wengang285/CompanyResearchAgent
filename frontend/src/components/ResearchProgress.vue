<script setup lang="ts">
import { computed } from 'vue'
import type { ResearchProgress } from '@/types'

const props = defineProps<{
  progress: ResearchProgress
  company: string
}>()

const agentSteps = [
  { name: 'Data Collector', label: '数据收集', icon: 'Search' },
  { name: 'Financial Analyzer', label: '财务分析', icon: 'DataLine' },
  { name: 'Market Analyzer', label: '市场分析', icon: 'TrendCharts' },
  { name: 'Report Generator', label: '报告生成', icon: 'Document' }
]

const currentStepIndex = computed(() => {
  const agentName = props.progress.currentAgent
  const index = agentSteps.findIndex(s => s.name === agentName)
  return index >= 0 ? index : 0
})

const formatTime = (seconds: number) => {
  if (seconds <= 0) return '计算中...'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins > 0) {
    return `约 ${mins} 分 ${secs} 秒`
  }
  return `约 ${secs} 秒`
}
</script>

<template>
  <div class="research-progress">
    <el-card class="progress-card" shadow="never">
      <div class="progress-header">
        <div class="company-info">
          <el-icon :size="32" class="pulse-icon"><Loading /></el-icon>
          <div>
            <h2 class="company-name">{{ company }}</h2>
            <p class="status-text">正在深度研究中...</p>
          </div>
        </div>
        <div class="time-estimate" v-if="progress.estimatedTime > 0">
          <el-icon><Timer /></el-icon>
          <span>{{ formatTime(progress.estimatedTime) }}</span>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="main-progress">
        <el-progress
          :percentage="progress.progress"
          :stroke-width="12"
          :format="(p: number) => `${p}%`"
          color="#e94560"
        />
      </div>

      <!-- 当前任务 -->
      <div class="current-task" v-if="progress.currentTask">
        <el-icon><Operation /></el-icon>
        <span>{{ progress.currentTask }}</span>
      </div>

      <!-- Agent 步骤 -->
      <div class="agent-steps">
        <div
          v-for="(step, index) in agentSteps"
          :key="step.name"
          class="step-item"
          :class="{
            'is-active': index === currentStepIndex,
            'is-completed': index < currentStepIndex,
            'is-pending': index > currentStepIndex
          }"
        >
          <div class="step-icon">
            <el-icon v-if="index < currentStepIndex" :size="20"><Check /></el-icon>
            <el-icon v-else-if="index === currentStepIndex" :size="20" class="rotating"><Loading /></el-icon>
            <span v-else class="step-number">{{ index + 1 }}</span>
          </div>
          <div class="step-content">
            <span class="step-label">{{ step.label }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 提示信息 -->
    <div class="tips">
      <el-alert
        title="研究过程说明"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <ul class="tips-list">
            <li>数据收集：从多个渠道搜索公司相关信息</li>
            <li>财务分析：分析财务报表，评估盈利能力和财务健康度</li>
            <li>市场分析：分析行业地位、竞争格局和发展前景</li>
            <li>报告生成：整合分析结果，生成专业研究报告</li>
          </ul>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<style scoped>
.research-progress {
  max-width: 800px;
  margin: 0 auto;
}

.progress-card {
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 24px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
}

.company-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.pulse-icon {
  color: var(--highlight-color);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.1); }
}

.company-name {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
  margin: 0 0 4px;
}

.status-text {
  color: var(--text-light);
  margin: 0;
  font-size: 14px;
}

.time-estimate {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-light);
  font-size: 14px;
  background: var(--bg-color);
  padding: 8px 16px;
  border-radius: 20px;
}

.main-progress {
  margin-bottom: 24px;
}

.current-task {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.1) 0%, rgba(15, 52, 96, 0.1) 100%);
  border-radius: 10px;
  color: var(--accent-color);
  font-size: 14px;
  margin-bottom: 30px;
}

.agent-steps {
  display: flex;
  justify-content: space-between;
  position: relative;
}

.agent-steps::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 40px;
  right: 40px;
  height: 2px;
  background: var(--border-color);
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 1;
}

.step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 2px solid var(--border-color);
  color: var(--text-light);
  font-weight: 600;
}

.step-item.is-completed .step-icon {
  background: #10b981;
  border-color: #10b981;
  color: white;
}

.step-item.is-active .step-icon {
  background: var(--highlight-color);
  border-color: var(--highlight-color);
  color: white;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.step-label {
  font-size: 13px;
  color: var(--text-light);
}

.step-item.is-active .step-label,
.step-item.is-completed .step-label {
  color: var(--text-color);
  font-weight: 500;
}

.tips {
  margin-top: 20px;
}

.tips-list {
  margin: 8px 0 0;
  padding-left: 20px;
  font-size: 13px;
  color: var(--text-light);
  line-height: 1.8;
}
</style>






