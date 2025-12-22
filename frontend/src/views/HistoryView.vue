<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { chatApi, type HistoryReport } from '@/api/chat'

const reports = ref<HistoryReport[]>([])
const isLoading = ref(true)

onMounted(async () => {
  try {
    const { reports: list } = await chatApi.getHistoryReports(50)
    reports.value = list
  } catch (e) {
    console.error('获取历史报告失败:', e)
  } finally {
    isLoading.value = false
  }
})

function getScoreColor(score: number) {
  if (score >= 8) return '#10b981'
  if (score >= 6) return '#f59e0b'
  return '#ef4444'
}

function getRecommendationClass(recommendation: string) {
  const map: Record<string, string> = {
    '买入': 'buy',
    '持有': 'hold',
    '卖出': 'sell',
    '观望': 'watch'
  }
  return map[recommendation] || 'watch'
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function openReport(taskId: string) {
  window.open(`/report/${taskId}`, '_blank')
}
</script>

<template>
  <div class="history-page">
    <div class="page-header">
      <router-link to="/" class="back-link">
        <el-icon><ArrowLeft /></el-icon>
        返回首页
      </router-link>
      <h1>历史研究报告</h1>
    </div>

    <div v-if="isLoading" class="loading">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="reports.length === 0" class="empty">
      <el-empty description="暂无历史报告" />
    </div>

    <div v-else class="report-list">
      <div
        v-for="report in reports"
        :key="report.task_id"
        class="report-item"
        @click="openReport(report.task_id)"
      >
        <div class="item-main">
          <h3>{{ report.company_name || report.company }}</h3>
          <p class="date">{{ formatDate(report.completed_at) }}</p>
        </div>
        <div class="item-metrics">
          <span class="score" :style="{ color: getScoreColor(report.overall_score) }">
            {{ report.overall_score }}/10
          </span>
          <span 
            class="recommendation"
            :class="getRecommendationClass(report.recommendation)"
          >
            {{ report.recommendation }}
          </span>
        </div>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  margin-bottom: 32px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--text-light);
  text-decoration: none;
  margin-bottom: 16px;
}

.back-link:hover {
  color: var(--primary-color);
}

.page-header h1 {
  font-size: 28px;
  margin: 0;
}

.loading {
  padding: 40px;
  background: white;
  border-radius: 12px;
}

.report-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.report-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.item-main {
  flex: 1;
}

.item-main h3 {
  margin: 0 0 4px;
  font-size: 18px;
}

.date {
  margin: 0;
  font-size: 14px;
  color: var(--text-light);
}

.item-metrics {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score {
  font-size: 20px;
  font-weight: 700;
}

.recommendation {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.recommendation.buy { background: #10b981; }
.recommendation.hold { background: #f59e0b; }
.recommendation.sell { background: #ef4444; }
.recommendation.watch { background: #6b7280; }

.arrow {
  color: var(--text-light);
}
</style>




