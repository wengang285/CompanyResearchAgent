<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  agentName: string
  status: string
  content: string
  messageType: string
  extraData?: Record<string, any> | null
}>()

// Agent 信息映射
const agentInfo = computed(() => {
  const map: Record<string, { icon: string; color: string; label: string }> = {
    'SearchAgent': { icon: '🔍', color: '#3b82f6', label: '信息猎手' },
    'DataAgent': { icon: '📊', color: '#8b5cf6', label: '数据管家' },
    'FinanceAgent': { icon: '💰', color: '#10b981', label: '财务顾问' },
    'MarketAgent': { icon: '📈', color: '#f59e0b', label: '市场分析师' },
    'InsightAgent': { icon: '💡', color: '#ec4899', label: '洞察专家' },
    'WriterAgent': { icon: '📝', color: '#06b6d4', label: '笔杆子' },
    'Analyzers': { icon: '🔬', color: '#6366f1', label: '分析师' }
  }
  return map[props.agentName] || { icon: '🤖', color: '#6b7280', label: props.agentName }
})

// 状态标签
const statusLabel = computed(() => {
  if (props.status === 'working') return '处理中...'
  if (props.status === 'completed') return '已完成'
  if (props.status === 'failed') return '失败'
  return ''
})

// 进度
const progress = computed(() => {
  return props.extraData?.progress || 0
})
</script>

<template>
  <div class="agent-bubble" :style="{ '--agent-color': agentInfo.color }">
    <div class="agent-header">
      <span class="agent-icon">{{ agentInfo.icon }}</span>
      <span class="agent-name">{{ agentInfo.label }}</span>
      <span v-if="status === 'working'" class="status-badge working">
        <el-icon class="spinning"><Loading /></el-icon>
        {{ statusLabel }}
      </span>
      <span v-else-if="status === 'completed'" class="status-badge completed">
        <el-icon><CircleCheck /></el-icon>
        {{ statusLabel }}
      </span>
    </div>
    
    <div class="agent-content">
      {{ content }}
    </div>
    
    <!-- 进度条 -->
    <div v-if="status === 'working' && progress > 0" class="progress-bar">
      <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
    </div>
    
    <!-- 额外数据展示 -->
    <div v-if="messageType === 'agent_result' && extraData" class="extra-info">
      <template v-if="extraData.score">
        <span class="score-badge">
          评分: {{ extraData.score }}/10
        </span>
      </template>
      <template v-if="extraData.recommendation">
        <span class="recommendation-badge">
          {{ extraData.recommendation }}
        </span>
      </template>
    </div>
  </div>
</template>

<style scoped>
.agent-bubble {
  background: white;
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid var(--agent-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  max-width: 500px;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.agent-icon {
  font-size: 20px;
}

.agent-name {
  font-weight: 600;
  color: var(--agent-color);
  font-size: 14px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: auto;
}

.status-badge.working {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.status-badge.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.agent-content {
  font-size: 14px;
  color: var(--text-color);
  line-height: 1.5;
}

.progress-bar {
  margin-top: 12px;
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--agent-color);
  transition: width 0.3s ease;
}

.extra-info {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.score-badge,
.recommendation-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.score-badge {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.recommendation-badge {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}
</style>




