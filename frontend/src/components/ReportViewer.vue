<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElLoading } from 'element-plus'
import { reportApi } from '@/api/research'
import type { Report, ReportSection } from '@/types'
import ScoreRadarChart from './charts/ScoreRadarChart.vue'
import ScoreGaugeChart from './charts/ScoreGaugeChart.vue'
import SwotChart from './charts/SwotChart.vue'
import RiskMatrixChart from './charts/RiskMatrixChart.vue'

const props = defineProps<{
  report: Report
  taskId: string
}>()

const activeSection = ref(0)
const isExporting = ref(false)

// 获取报告章节
function getSections(): ReportSection[] {
  if (props.report.sections) {
    return props.report.sections
  }
  if (props.report.content?.sections) {
    return props.report.content.sections
  }
  return []
}

// 获取 metadata
function getMetadata() {
  if (props.report.metadata) return props.report.metadata
  if (props.report.content?.metadata) return props.report.content.metadata
  return {}
}

// 获取报告基本信息
const reportInfo = computed(() => {
  const metadata = getMetadata()
  return {
    company: metadata.company_name || metadata.company || props.report.company || '',
    stockCode: metadata.stock_code || props.report.stock_code || '',
    researchDate: metadata.research_date || props.report.research_date || new Date().toISOString(),
    industry: metadata.industry || '',
    overallScore: metadata.overall_score || 5,
    recommendation: metadata.recommendation || '观望'
  }
})

// 获取雷达图数据
const radarScores = computed(() => {
  const sections = getSections()
  const scores = []
  
  // 从各章节提取评分
  for (const section of sections) {
    if (section.id === 'financial_analysis' && section.overall_score) {
      scores.push({ name: '财务分析', score: section.overall_score })
    }
    if (section.id === 'market_analysis' && section.overall_score) {
      scores.push({ name: '市场分析', score: section.overall_score })
    }
    if (section.id === 'risk_assessment') {
      // 风险评分：风险越少分数越高
      const riskCount = section.risks?.length || 0
      scores.push({ name: '风险控制', score: Math.max(10 - riskCount * 2, 3) })
    }
    if (section.id === 'investment_insights') {
      scores.push({ name: '投资价值', score: reportInfo.value.overallScore })
    }
  }
  
  // 确保至少有基础数据
  if (scores.length < 4) {
    const defaultScores = [
      { name: '财务分析', score: 6 },
      { name: '市场分析', score: 6 },
      { name: '风险控制', score: 6 },
      { name: '投资价值', score: reportInfo.value.overallScore },
      { name: '成长潜力', score: 6 }
    ]
    return defaultScores
  }
  
  scores.push({ name: '成长潜力', score: Math.round((scores.reduce((a, b) => a + b.score, 0) / scores.length)) })
  return scores
})

// 获取 SWOT 数据
const swotData = computed(() => {
  const sections = getSections()
  const marketSection = sections.find(s => s.id === 'market_analysis')
  
  if (marketSection?.swot) {
    return marketSection.swot
  }
  
  // 尝试从 subsections 提取
  if (marketSection?.subsections) {
    const swotSub = marketSection.subsections.find(s => 
      s.title?.includes('SWOT') || s.title?.includes('swot')
    )
    if (swotSub) {
      return {
        strengths: swotSub.strengths || [],
        weaknesses: swotSub.weaknesses || [],
        opportunities: swotSub.opportunities || [],
        threats: swotSub.threats || []
      }
    }
  }
  
  return {
    strengths: [],
    weaknesses: [],
    opportunities: [],
    threats: []
  }
})

// 获取风险数据
const riskData = computed(() => {
  const sections = getSections()
  const riskSection = sections.find(s => s.id === 'risk_assessment')
  
  if (riskSection?.risks) {
    return riskSection.risks.map(r => ({
      type: typeof r === 'object' ? r.type : '风险',
      description: typeof r === 'object' ? r.description : r,
      severity: typeof r === 'object' ? r.severity : '中'
    }))
  }
  
  return []
})

// 是否显示图表
const hasChartData = computed(() => {
  return radarScores.value.length > 0 || 
         Object.values(swotData.value).some((arr) => Array.isArray(arr) && arr.length > 0) ||
         riskData.value.length > 0
})

// 格式化日期
function formatDate(dateStr: string) {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch {
    return dateStr
  }
}

// 格式化评分
function formatScore(score: number | undefined) {
  if (score === undefined) return '-'
  return `${score}/10`
}

// 获取评分颜色
function getScoreColor(score: number | undefined) {
  if (score === undefined) return '#6b7280'
  if (score >= 8) return '#10b981'
  if (score >= 6) return '#f59e0b'
  return '#ef4444'
}

// 导出 PDF
async function exportPdf() {
  isExporting.value = true
  const loading = ElLoading.service({
    lock: true,
    text: '正在生成 PDF 报告...',
    background: 'rgba(0, 0, 0, 0.7)'
  })
  
  try {
    // 先从任务生成报告记录
    const result = await reportApi.generateFromTask(props.taskId)
    
    // 下载 PDF
    const blob = await reportApi.downloadPdf(result.report_id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${reportInfo.value.company}_研究报告.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('PDF 导出成功！')
  } catch (e) {
    console.error('PDF 导出失败:', e)
    ElMessage.error('PDF 导出失败，请重试')
  } finally {
    loading.close()
    isExporting.value = false
  }
}
</script>

<template>
  <div class="report-viewer">
    <!-- 报告头部 -->
    <div class="report-header">
      <div class="header-content">
        <div class="company-badge">
          <el-icon :size="32"><OfficeBuilding /></el-icon>
        </div>
        <div class="header-info">
          <h1 class="report-title">{{ reportInfo.company }}</h1>
          <p class="report-subtitle">深度研究报告</p>
          <div class="report-meta">
            <el-tag v-if="reportInfo.stockCode" type="info" effect="plain">
              {{ reportInfo.stockCode }}
            </el-tag>
            <el-tag v-if="reportInfo.industry" type="info" effect="plain">
              {{ reportInfo.industry }}
            </el-tag>
            <span class="meta-date">
              <el-icon><Calendar /></el-icon>
              {{ formatDate(reportInfo.researchDate) }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- 评分和评级 -->
      <div class="header-rating">
        <div class="rating-score">
          <span class="score-value" :style="{ color: getScoreColor(reportInfo.overallScore) }">
            {{ reportInfo.overallScore }}
          </span>
          <span class="score-label">综合评分</span>
        </div>
        <div class="rating-recommendation">
          <span 
            class="recommendation-badge"
            :class="getRecommendationClass(reportInfo.recommendation)"
          >
            {{ reportInfo.recommendation }}
          </span>
          <span class="recommendation-label">投资建议</span>
        </div>
      </div>
      
      <div class="header-actions">
        <el-button
          type="primary"
          size="large"
          :loading="isExporting"
          @click="exportPdf"
        >
          <el-icon><Download /></el-icon>
          导出 PDF
        </el-button>
      </div>
    </div>

    <!-- 图表概览区域 -->
    <div v-if="hasChartData" class="charts-overview">
      <h3 class="charts-title">
        <el-icon><DataAnalysis /></el-icon>
        分析图表概览
      </h3>
      <div class="charts-grid">
        <!-- 综合评分仪表盘 -->
        <div class="chart-card">
          <ScoreGaugeChart 
            :score="reportInfo.overallScore" 
            :recommendation="reportInfo.recommendation"
          />
        </div>
        
        <!-- 多维评分雷达图 -->
        <div class="chart-card">
          <ScoreRadarChart 
            :scores="radarScores" 
            title="多维度评分分析"
          />
        </div>
        
        <!-- SWOT 分析 -->
        <div class="chart-card chart-wide">
          <SwotChart :data="swotData" />
        </div>
        
        <!-- 风险矩阵 -->
        <div v-if="riskData.length > 0" class="chart-card">
          <RiskMatrixChart :risks="riskData" />
        </div>
      </div>
    </div>

    <!-- 报告主体 -->
    <div class="report-body">
      <!-- 左侧目录导航 -->
      <aside class="report-toc">
        <div class="toc-header">
          <el-icon><Document /></el-icon>
          <span>目录</span>
        </div>
        <nav class="toc-nav">
          <a
            v-for="(section, index) in getSections()"
            :key="index"
            :class="['toc-item', { active: activeSection === index }]"
            @click="activeSection = index"
          >
            <span class="toc-number">{{ index + 1 }}</span>
            <span class="toc-title">{{ section.title }}</span>
          </a>
        </nav>
      </aside>

      <!-- 右侧内容区 -->
      <main class="report-content">
        <template v-for="(section, index) in getSections()" :key="index">
          <article
            v-show="activeSection === index"
            class="section-article"
          >
            <!-- 章节标题 -->
            <header class="section-header">
              <h2 class="section-title">
                <span class="section-number">{{ index + 1 }}</span>
                {{ section.title }}
              </h2>
              <div v-if="section.overall_score" class="section-score">
                <span class="score-label">综合评分</span>
                <span 
                  class="score-value"
                  :style="{ color: getScoreColor(section.overall_score) }"
                >
                  {{ formatScore(section.overall_score) }}
                </span>
              </div>
            </header>

            <!-- 章节主内容 -->
            <div v-if="section.content" class="section-main-content">
              <p>{{ section.content }}</p>
            </div>

            <!-- 关键要点 -->
            <div v-if="section.key_points?.length" class="key-points-box">
              <h4 class="box-title">
                <el-icon><Star /></el-icon>
                核心要点
              </h4>
              <ul class="key-points-list">
                <li v-for="(point, i) in section.key_points" :key="i">
                  {{ point }}
                </li>
              </ul>
            </div>

            <!-- 子章节 -->
            <div v-if="section.subsections?.length" class="subsections">
              <div
                v-for="(sub, i) in section.subsections"
                :key="i"
                class="subsection-card"
              >
                <div class="subsection-header">
                  <h3 class="subsection-title">{{ sub.title }}</h3>
                  <el-tag
                    v-if="sub.score"
                    :color="getScoreColor(sub.score)"
                    effect="dark"
                    size="small"
                  >
                    {{ formatScore(sub.score) }}
                  </el-tag>
                </div>
                <p v-if="sub.content" class="subsection-content">
                  {{ sub.content }}
                </p>
              </div>
            </div>

            <!-- 风险列表 -->
            <div v-if="section.risks?.length" class="risks-box">
              <h4 class="box-title">
                <el-icon><WarningFilled /></el-icon>
                风险因素
              </h4>
              <div class="risk-list">
                <div v-for="(risk, i) in section.risks" :key="i" class="risk-item">
                  <el-tag type="danger" size="small" effect="dark">
                    {{ typeof risk === 'object' ? risk.type : '风险' }}
                  </el-tag>
                  <span class="risk-desc">
                    {{ typeof risk === 'object' ? risk.description : risk }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 投资建议 -->
            <div v-if="section.recommendation" class="recommendation-box">
              <div class="recommendation-header">
                <span 
                  class="recommendation-badge"
                  :class="getRecommendationClass(section.recommendation)"
                >
                  {{ section.recommendation }}
                </span>
              </div>
              <p v-if="section.reasoning" class="recommendation-reasoning">
                {{ section.reasoning }}
              </p>
              
              <div v-if="section.catalysts?.length" class="catalysts">
                <h5>上涨催化剂</h5>
                <div class="catalyst-tags">
                  <el-tag
                    v-for="(catalyst, i) in section.catalysts"
                    :key="i"
                    type="success"
                    effect="light"
                  >
                    {{ catalyst }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 章节小结 -->
            <div v-if="section.summary" class="section-summary">
              <el-alert type="info" :closable="false" show-icon>
                <template #title>
                  <strong>小结</strong>
                </template>
                {{ section.summary }}
              </el-alert>
            </div>
          </article>
        </template>

        <!-- 章节导航 -->
        <div class="section-navigation">
          <el-button
            v-if="activeSection > 0"
            @click="activeSection--"
          >
            <el-icon><ArrowLeft /></el-icon>
            上一章节
          </el-button>
          <span class="nav-indicator">
            {{ activeSection + 1 }} / {{ getSections().length }}
          </span>
          <el-button
            v-if="activeSection < getSections().length - 1"
            type="primary"
            @click="activeSection++"
          >
            下一章节
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </main>
    </div>

    <!-- 底部免责声明 -->
    <footer class="report-footer">
      <p>本报告由 AI Agent 系统自动生成，仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。</p>
    </footer>
  </div>
</template>

<script lang="ts">
function getRecommendationClass(recommendation: string) {
  const map: Record<string, string> = {
    '买入': 'buy',
    '持有': 'hold',
    '卖出': 'sell',
    '观望': 'watch'
  }
  return map[recommendation] || 'watch'
}
</script>

<style scoped>
.report-viewer {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 报告头部 */
.report-header {
  display: flex;
  align-items: center;
  padding: 32px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 20px;
  color: white;
  gap: 24px;
}

.header-content {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.company-badge {
  width: 64px;
  height: 64px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.report-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px;
}

.report-subtitle {
  font-size: 16px;
  opacity: 0.8;
  margin: 0 0 16px;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.meta-date {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  opacity: 0.8;
}

.header-rating {
  display: flex;
  gap: 24px;
  margin-left: auto;
  margin-right: 24px;
}

.rating-score,
.rating-recommendation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.rating-score .score-value {
  font-size: 36px;
  font-weight: 700;
}

.rating-score .score-label,
.rating-recommendation .recommendation-label {
  font-size: 12px;
  opacity: 0.7;
}

.rating-recommendation .recommendation-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.rating-recommendation .recommendation-badge.buy {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.rating-recommendation .recommendation-badge.hold {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.rating-recommendation .recommendation-badge.sell {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.rating-recommendation .recommendation-badge.watch {
  background: rgba(107, 114, 128, 0.2);
  color: #9ca3af;
}

.header-actions {
  flex-shrink: 0;
}

/* 图表概览区域 */
.charts-overview {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.charts-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 20px;
}

.charts-title .el-icon {
  color: #6366f1;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-card {
  background: #fafafa;
  border-radius: 12px;
  overflow: hidden;
}

.chart-card.chart-wide {
  grid-column: span 2;
}

@media (max-width: 900px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-card.chart-wide {
    grid-column: span 1;
  }
}

/* 报告主体 */
.report-body {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 24px;
}

/* 目录 */
.report-toc {
  background: white;
  border-radius: 16px;
  padding: 24px;
  height: fit-content;
  position: sticky;
  top: 88px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.toc-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--border-color);
}

.toc-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.toc-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  color: var(--text-color);
}

.toc-item:hover {
  background: var(--bg-color);
}

.toc-item.active {
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.1) 0%, rgba(15, 52, 96, 0.1) 100%);
  color: var(--primary-color);
}

.toc-number {
  width: 24px;
  height: 24px;
  background: var(--border-color);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.toc-item.active .toc-number {
  background: var(--primary-color);
  color: white;
}

.toc-title {
  font-size: 14px;
}

/* 内容区 */
.report-content {
  min-width: 0;
}

.section-article {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--border-color);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
  margin: 0;
}

.section-number {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
  color: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.section-score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.score-label {
  font-size: 12px;
  color: var(--text-light);
}

.score-value {
  font-size: 24px;
  font-weight: 700;
}

.section-main-content {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-color);
  margin-bottom: 24px;
}

.section-main-content p {
  margin: 0;
  white-space: pre-wrap;
}

/* 关键要点 */
.key-points-box,
.risks-box {
  background: var(--bg-color);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.box-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-color);
  margin: 0 0 16px;
}

.key-points-list {
  margin: 0;
  padding-left: 20px;
}

.key-points-list li {
  margin-bottom: 8px;
  line-height: 1.6;
}

/* 子章节 */
.subsections {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.subsection-card {
  background: var(--bg-color);
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid var(--accent-color);
}

.subsection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.subsection-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent-color);
  margin: 0;
}

.subsection-content {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-color);
  white-space: pre-wrap;
}

/* 风险 */
.risk-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.risk-desc {
  font-size: 14px;
  line-height: 1.6;
}

/* 投资建议 */
.recommendation-box {
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.05) 0%, rgba(15, 52, 96, 0.05) 100%);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.recommendation-header {
  margin-bottom: 16px;
}

.recommendation-badge {
  display: inline-block;
  padding: 8px 24px;
  border-radius: 20px;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.recommendation-badge.buy {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.recommendation-badge.hold {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.recommendation-badge.sell {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.recommendation-badge.watch {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.recommendation-reasoning {
  font-size: 15px;
  line-height: 1.8;
  margin: 0 0 20px;
}

.catalysts h5 {
  font-size: 14px;
  margin: 0 0 12px;
  color: var(--primary-color);
}

.catalyst-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 章节小结 */
.section-summary {
  margin-top: 24px;
}

/* 章节导航 */
.section-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.nav-indicator {
  font-size: 14px;
  color: var(--text-light);
}

/* 底部 */
.report-footer {
  text-align: center;
  padding: 20px;
  background: var(--bg-color);
  border-radius: 12px;
}

.report-footer p {
  margin: 0;
  font-size: 13px;
  color: var(--text-light);
}

/* 响应式 */
@media (max-width: 900px) {
  .report-body {
    grid-template-columns: 1fr;
  }
  
  .report-toc {
    position: static;
  }
  
  .report-header {
    flex-direction: column;
    gap: 20px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .report-meta {
    justify-content: center;
  }
}
</style>
