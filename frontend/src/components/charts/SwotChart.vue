<script setup lang="ts">
interface SwotItem {
  item: string
  detail?: string
}

type SwotItemType = string | SwotItem

interface SwotData {
  strengths: SwotItemType[]
  weaknesses: SwotItemType[]
  opportunities: SwotItemType[]
  threats: SwotItemType[]
}

const props = defineProps<{
  data: SwotData
}>()

// 格式化 SWOT 项目，支持字符串和字典两种格式
function formatSwotItem(item: SwotItemType): string {
  if (typeof item === 'string') {
    return item
  }
  // 字典格式: { item: "...", detail: "..." }
  const name = item.item || ''
  const detail = item.detail || ''
  return detail ? `${name}：${detail}` : name
}
</script>

<template>
  <div class="swot-chart">
    <h4 class="chart-title">SWOT 分析</h4>
    <div class="swot-grid">
      <!-- 优势 Strengths -->
      <div class="swot-quadrant strengths">
        <div class="quadrant-header">
          <span class="quadrant-icon">💪</span>
          <span class="quadrant-title">优势 (S)</span>
        </div>
        <ul class="quadrant-list">
          <li v-for="(item, i) in data.strengths" :key="i">{{ formatSwotItem(item) }}</li>
        </ul>
        <div v-if="!data.strengths?.length" class="empty-hint">暂无数据</div>
      </div>
      
      <!-- 劣势 Weaknesses -->
      <div class="swot-quadrant weaknesses">
        <div class="quadrant-header">
          <span class="quadrant-icon">⚠️</span>
          <span class="quadrant-title">劣势 (W)</span>
        </div>
        <ul class="quadrant-list">
          <li v-for="(item, i) in data.weaknesses" :key="i">{{ formatSwotItem(item) }}</li>
        </ul>
        <div v-if="!data.weaknesses?.length" class="empty-hint">暂无数据</div>
      </div>
      
      <!-- 机会 Opportunities -->
      <div class="swot-quadrant opportunities">
        <div class="quadrant-header">
          <span class="quadrant-icon">🚀</span>
          <span class="quadrant-title">机会 (O)</span>
        </div>
        <ul class="quadrant-list">
          <li v-for="(item, i) in data.opportunities" :key="i">{{ formatSwotItem(item) }}</li>
        </ul>
        <div v-if="!data.opportunities?.length" class="empty-hint">暂无数据</div>
      </div>
      
      <!-- 威胁 Threats -->
      <div class="swot-quadrant threats">
        <div class="quadrant-header">
          <span class="quadrant-icon">🔥</span>
          <span class="quadrant-title">威胁 (T)</span>
        </div>
        <ul class="quadrant-list">
          <li v-for="(item, i) in data.threats" :key="i">{{ formatSwotItem(item) }}</li>
        </ul>
        <div v-if="!data.threats?.length" class="empty-hint">暂无数据</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.swot-chart {
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

.swot-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.swot-quadrant {
  border-radius: 12px;
  padding: 16px;
  min-height: 150px;
}

.strengths {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.weaknesses {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.opportunities {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.threats {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.quadrant-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.quadrant-icon {
  font-size: 20px;
}

.quadrant-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.strengths .quadrant-title { color: #059669; }
.weaknesses .quadrant-title { color: #d97706; }
.opportunities .quadrant-title { color: #2563eb; }
.threats .quadrant-title { color: #dc2626; }

.quadrant-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.quadrant-list li {
  position: relative;
  padding-left: 16px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
}

.quadrant-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.strengths .quadrant-list li::before { background: #10b981; }
.weaknesses .quadrant-list li::before { background: #f59e0b; }
.opportunities .quadrant-list li::before { background: #3b82f6; }
.threats .quadrant-list li::before { background: #ef4444; }

.empty-hint {
  color: #9ca3af;
  font-size: 13px;
  text-align: center;
  padding: 20px;
}

@media (max-width: 640px) {
  .swot-grid {
    grid-template-columns: 1fr;
  }
}
</style>




