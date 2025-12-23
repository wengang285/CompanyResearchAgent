<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  agentName: string
  status: string
  content: string
  messageType: string
  extraData?: Record<string, any> | null
}>()

// 是否正在流式输出
const isStreaming = computed(() => {
  return props.status === 'streaming' || props.messageType === 'streaming'
})

// 折叠状态 - 流式输出默认折叠，其他默认展开
const isCollapsed = ref(isStreaming.value)

// 是否显示折叠按钮（当有内容时）
const showCollapseButton = computed(() => {
  return props.content && props.content.trim().length > 0
})

// 显示的内容
const displayContent = computed(() => {
  return props.content || ''
})

// 内容预览（用于折叠时的提示）
const contentPreview = computed(() => {
  if (!props.content) return '正在生成内容...'
  // 提取前80个字符作为预览，去除换行和多余空格
  const preview = props.content
    .replace(/\n+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 80)
  return preview.length < props.content.length ? preview + '...' : preview
})

// 切换折叠状态
function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

// 监听流式输出状态变化
watch(isStreaming, (streaming) => {
  // 如果开始流式输出，默认折叠
  if (streaming) {
    isCollapsed.value = true
  }
  // 如果流式输出完成，保持当前折叠状态（不自动展开）
})

// Agent 信息映射
const agentInfo = computed(() => {
  const map: Record<string, { icon: string; color: string; label: string; avatarBg: string }> = {
    'SearchAgent': { 
      icon: '🔍', 
      color: '#3b82f6', 
      label: '信息猎手',
      avatarBg: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
    },
    'DataAgent': { 
      icon: '📊', 
      color: '#8b5cf6', 
      label: '数据管家',
      avatarBg: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
    },
    'FinanceAgent': { 
      icon: '💰', 
      color: '#10b981', 
      label: '财务顾问',
      avatarBg: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
    },
    'MarketAgent': { 
      icon: '📈', 
      color: '#f59e0b', 
      label: '市场分析师',
      avatarBg: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
    },
    'InsightAgent': { 
      icon: '💡', 
      color: '#ec4899', 
      label: '洞察专家',
      avatarBg: 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)'
    },
    'WriterAgent': { 
      icon: '📝', 
      color: '#06b6d4', 
      label: '笔杆子',
      avatarBg: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)'
    },
    'Analyzers': { 
      icon: '🔬', 
      color: '#6366f1', 
      label: '分析师',
      avatarBg: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)'
    }
  }
  return map[props.agentName] || { 
    icon: '🤖', 
    color: '#6b7280', 
    label: props.agentName,
    avatarBg: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)'
  }
})

// 状态标签
const statusLabel = computed(() => {
  if (props.status === 'working') return '处理中...'
  if (props.status === 'streaming') return '生成中...'
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
  <div 
    class="agent-bubble" 
    :class="{ 'streaming': isStreaming }"
    :style="{ '--agent-color': agentInfo.color }"
  >
    <div class="agent-header">
      <!-- Agent 头像 -->
      <div 
        class="agent-avatar" 
        :style="{ background: agentInfo.avatarBg }"
      >
        <span class="avatar-icon">{{ agentInfo.icon }}</span>
      </div>
      
      <div class="agent-info">
        <span class="agent-name">{{ agentInfo.label }}</span>
        <span v-if="status === 'working' || status === 'streaming'" class="status-badge working">
          <el-icon class="spinning"><Loading /></el-icon>
          {{ statusLabel }}
        </span>
        <span v-else-if="status === 'completed'" class="status-badge completed">
          <el-icon><CircleCheck /></el-icon>
          {{ statusLabel }}
        </span>
      </div>
    </div>
    
    <div class="agent-content-wrapper">
      <!-- 折叠状态显示 -->
      <div v-if="isCollapsed && showCollapseButton" class="agent-content-collapsed">
        <div class="content-preview">
          <span v-if="isStreaming" class="preview-label">正在生成中...</span>
          <span v-else class="preview-label">内容预览：</span>
          <span class="preview-text">{{ contentPreview }}</span>
        </div>
        <el-button 
          text 
          size="small" 
          @click="toggleCollapse"
          class="expand-btn"
        >
          <el-icon><ArrowDown /></el-icon>
          <span>展开查看</span>
        </el-button>
      </div>
      
      <!-- 展开状态显示 -->
      <div 
        v-else-if="showCollapseButton" 
        class="agent-content"
        :class="{ 'streaming': isStreaming }"
      >
        <span v-if="isStreaming" class="streaming-content">
          {{ displayContent }}
          <span class="cursor">|</span>
        </span>
        <span v-else class="content-text">{{ displayContent }}</span>
      </div>
      
      <!-- 折叠/展开控制按钮 -->
      <div v-if="showCollapseButton" class="collapse-control">
        <el-button 
          text 
          size="small" 
          @click="toggleCollapse"
          class="collapse-btn"
        >
          <el-icon>
            <ArrowUp v-if="!isCollapsed" />
            <ArrowDown v-else />
          </el-icon>
          <span>{{ isCollapsed ? '展开' : '折叠' }}</span>
        </el-button>
      </div>
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
  border-radius: 16px;
  padding: 16px;
  border-left: 4px solid var(--agent-color);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  max-width: 500px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.agent-bubble::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--agent-color);
  opacity: 0.8;
  transition: width 0.3s ease;
}

.agent-bubble:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.agent-bubble:hover::before {
  width: 6px;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

/* Agent 头像 */
.agent-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15), 0 0 0 2px rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.agent-bubble:hover .agent-avatar {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 0 0 2px rgba(255, 255, 255, 0.2);
}

/* 头像高光效果 */
.agent-avatar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.4), transparent 70%);
  pointer-events: none;
  z-index: 1;
}

/* 头像底部阴影 */
.agent-avatar::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 20%;
  right: 20%;
  height: 4px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 50%;
  filter: blur(2px);
  z-index: 0;
}

.avatar-icon {
  font-size: 24px;
  z-index: 2;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.3));
  position: relative;
  animation: float 3s ease-in-out infinite;
}

/* 头像图标浮动动画 */
@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}

/* 流式输出时的头像动画 - 通过动态类名控制 */
.agent-bubble.streaming .agent-avatar {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15), 0 0 0 2px rgba(255, 255, 255, 0.1);
  }
  50% {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15), 0 0 0 4px var(--agent-color);
  }
}

.agent-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.agent-name {
  font-weight: 600;
  color: var(--agent-color);
  font-size: 15px;
  white-space: nowrap;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  white-space: nowrap;
  flex-shrink: 0;
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

.agent-content-wrapper {
  position: relative;
}

/* 折叠状态样式 */
.agent-content-collapsed {
  padding: 12px;
  background: var(--bg-color);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.content-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
}

.preview-label {
  font-size: 12px;
  color: var(--text-light);
  font-weight: 500;
}

.preview-text {
  font-size: 13px;
  color: var(--text-color);
  line-height: 1.4;
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.expand-btn {
  width: 100%;
  justify-content: center;
  color: var(--agent-color);
  font-size: 12px;
  padding: 4px;
}

.expand-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

/* 展开状态样式 */
.agent-content {
  font-size: 14px;
  color: var(--text-color);
  line-height: 1.6;
  max-height: 500px;
  overflow-y: auto;
  padding: 12px;
  background: var(--bg-color);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.agent-content.streaming {
  background: rgba(0, 0, 0, 0.02);
  border-color: var(--agent-color);
  border-width: 1.5px;
}

.content-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.collapse-control {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.collapse-btn {
  color: var(--agent-color);
  font-size: 12px;
  padding: 4px 8px;
  transition: all 0.2s;
}

.collapse-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  transform: translateY(-1px);
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

.streaming-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.cursor {
  display: inline-block;
  animation: blink 1s infinite;
  color: var(--agent-color);
  font-weight: bold;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>




