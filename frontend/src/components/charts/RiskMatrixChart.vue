<script setup lang="ts">
import { computed } from 'vue'

interface RiskItem {
  type: string
  description: string
  severity?: string  // 高/中/低
}

const props = defineProps<{
  risks: RiskItem[]
}>()

// 按严重程度分组
const groupedRisks = computed(() => {
  const groups = {
    high: [] as RiskItem[],
    medium: [] as RiskItem[],
    low: [] as RiskItem[]
  }
  
  props.risks.forEach(risk => {
    const severity = risk.severity || '中'  // 默认中风险
    if (severity === '高' || severity === 'high') {
      groups.high.push(risk)
    } else if (severity === '中' || severity === 'medium') {
      groups.medium.push(risk)
    } else {
      groups.low.push(risk)
    }
  })
  
  return groups
})
</script>

<template>
  <div class="risk-matrix-chart">
    <h4 class="chart-title">风险评估矩阵</h4>
    
    <div class="risk-levels">
      <!-- 高风险 -->
      <div class="risk-level high">
        <div class="level-header">
          <span class="level-icon">🔴</span>
          <span class="level-title">高风险</span>
          <span class="level-count">{{ groupedRisks.high.length }}</span>
        </div>
        <div class="level-items">
          <div v-for="(risk, i) in groupedRisks.high" :key="i" class="risk-item">
            <span class="risk-type">{{ risk.type }}</span>
            <span class="risk-desc">{{ risk.description }}</span>
          </div>
          <div v-if="!groupedRisks.high.length" class="empty-hint">暂无高风险因素</div>
        </div>
      </div>
      
      <!-- 中风险 -->
      <div class="risk-level medium">
        <div class="level-header">
          <span class="level-icon">🟡</span>
          <span class="level-title">中风险</span>
          <span class="level-count">{{ groupedRisks.medium.length }}</span>
        </div>
        <div class="level-items">
          <div v-for="(risk, i) in groupedRisks.medium" :key="i" class="risk-item">
            <span class="risk-type">{{ risk.type }}</span>
            <span class="risk-desc">{{ risk.description }}</span>
          </div>
          <div v-if="!groupedRisks.medium.length" class="empty-hint">暂无中风险因素</div>
        </div>
      </div>
      
      <!-- 低风险 -->
      <div class="risk-level low">
        <div class="level-header">
          <span class="level-icon">🟢</span>
          <span class="level-title">低风险</span>
          <span class="level-count">{{ groupedRisks.low.length }}</span>
        </div>
        <div class="level-items">
          <div v-for="(risk, i) in groupedRisks.low" :key="i" class="risk-item">
            <span class="risk-type">{{ risk.type }}</span>
            <span class="risk-desc">{{ risk.description }}</span>
          </div>
          <div v-if="!groupedRisks.low.length" class="empty-hint">暂无低风险因素</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.risk-matrix-chart {
  background: white;
  border-radius: 12px;
  padding: 24px;
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 20px;
  text-align: center;
}

.risk-levels {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.risk-level {
  border-radius: 12px;
  overflow: hidden;
}

.risk-level.high {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(239, 68, 68, 0.03) 100%);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.risk-level.medium {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(245, 158, 11, 0.03) 100%);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.risk-level.low {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(16, 185, 129, 0.03) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.level-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.level-icon {
  font-size: 16px;
}

.level-title {
  font-size: 14px;
  font-weight: 600;
}

.high .level-title { color: #dc2626; }
.medium .level-title { color: #d97706; }
.low .level-title { color: #059669; }

.level-count {
  margin-left: auto;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}

.high .level-count { background: rgba(239, 68, 68, 0.2); color: #dc2626; }
.medium .level-count { background: rgba(245, 158, 11, 0.2); color: #d97706; }
.low .level-count { background: rgba(16, 185, 129, 0.2); color: #059669; }

.level-items {
  padding: 12px 16px;
}

.risk-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px dashed rgba(0, 0, 0, 0.05);
}

.risk-item:last-child {
  border-bottom: none;
}

.risk-type {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.05);
  color: #6b7280;
}

.risk-desc {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
}

.empty-hint {
  color: #9ca3af;
  font-size: 13px;
  text-align: center;
  padding: 8px;
}
</style>



