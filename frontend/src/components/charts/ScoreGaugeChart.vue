<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { GaugeChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([GaugeChart, CanvasRenderer])

const props = defineProps<{
  score: number
  maxScore?: number
  title?: string
  recommendation?: string
}>()

const getColor = (score: number) => {
  if (score >= 8) return '#10b981'
  if (score >= 6) return '#f59e0b'
  return '#ef4444'
}

const option = computed(() => {
  const max = props.maxScore || 10
  const value = props.score
  const color = getColor(value)
  
  return {
    series: [{
      type: 'gauge',
      startAngle: 200,
      endAngle: -20,
      min: 0,
      max: max,
      splitNumber: 10,
      itemStyle: {
        color: color
      },
      progress: {
        show: true,
        width: 20,
        roundCap: true
      },
      pointer: {
        show: false
      },
      axisLine: {
        lineStyle: {
          width: 20,
          color: [[1, '#f3f4f6']]
        },
        roundCap: true
      },
      axisTick: {
        show: false
      },
      splitLine: {
        show: false
      },
      axisLabel: {
        show: false
      },
      anchor: {
        show: false
      },
      title: {
        show: false
      },
      detail: {
        valueAnimation: true,
        width: '60%',
        lineHeight: 40,
        borderRadius: 8,
        offsetCenter: [0, '-5%'],
        fontSize: 48,
        fontWeight: 'bold',
        formatter: '{value}',
        color: color
      },
      data: [{
        value: value
      }]
    }]
  }
})
</script>

<template>
  <div class="score-gauge-chart">
    <VChart :option="option" autoresize class="chart" />
    <div class="gauge-info">
      <span class="gauge-label">综合评分</span>
      <span 
        v-if="recommendation" 
        class="recommendation-badge"
        :class="recommendation"
      >
        {{ recommendation }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.score-gauge-chart {
  background: white;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.chart {
  height: 200px;
  width: 100%;
}

.gauge-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-top: -20px;
}

.gauge-label {
  font-size: 14px;
  color: #6b7280;
}

.recommendation-badge {
  padding: 6px 20px;
  border-radius: 20px;
  font-size: 16px;
  font-weight: 600;
}

.recommendation-badge.买入,
.recommendation-badge.buy {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.recommendation-badge.持有,
.recommendation-badge.hold {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.recommendation-badge.卖出,
.recommendation-badge.sell {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.recommendation-badge.观望,
.recommendation-badge.watch {
  background: rgba(107, 114, 128, 0.15);
  color: #6b7280;
}
</style>




