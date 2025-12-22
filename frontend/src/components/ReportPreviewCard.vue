<script setup lang="ts">
import type { ReportPreview } from '@/api/chat'

const props = defineProps<{
  preview: ReportPreview
}>()

// 获取评分颜色
function getScoreColor(score: number) {
  if (score >= 8) return '#10b981'
  if (score >= 6) return '#f59e0b'
  return '#ef4444'
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

// 打开报告
function openReport() {
  window.open(props.preview.report_url, '_blank')
}
</script>

<template>
  <div class="report-preview-card">
    <div class="card-header">
      <div class="success-icon">✅</div>
      <div class="header-text">
        <h4>研究报告已生成</h4>
        <p>{{ preview.company_name || preview.company }}</p>
      </div>
    </div>
    
    <div class="card-body">
      <!-- 评分和评级 -->
      <div class="metrics">
        <div class="metric-item">
          <span class="metric-label">综合评分</span>
          <span class="metric-value" :style="{ color: getScoreColor(preview.overall_score) }">
            {{ preview.overall_score }}/10
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">投资评级</span>
          <span 
            class="recommendation-tag"
            :class="getRecommendationClass(preview.recommendation)"
          >
            {{ preview.recommendation }}
          </span>
        </div>
      </div>
      
      <!-- 执行摘要 -->
      <div v-if="preview.executive_summary" class="summary">
        <p>{{ preview.executive_summary }}...</p>
      </div>
    </div>
    
    <div class="card-footer">
      <el-button type="primary" size="large" @click="openReport">
        <el-icon><Document /></el-icon>
        查看完整报告
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.report-preview-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  max-width: 450px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.success-icon {
  font-size: 32px;
}

.header-text h4 {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 600;
}

.header-text p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.card-body {
  padding: 20px;
}

.metrics {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 12px;
  color: var(--text-light);
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
}

.recommendation-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
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

.summary {
  background: var(--bg-color);
  border-radius: 8px;
  padding: 12px;
}

.summary p {
  margin: 0;
  font-size: 14px;
  color: var(--text-color);
  line-height: 1.6;
}

.card-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.card-footer .el-button {
  width: 100%;
}
</style>




