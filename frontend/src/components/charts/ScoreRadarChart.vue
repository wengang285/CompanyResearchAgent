<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

// 注册 ECharts 组件
use([RadarChart, TooltipComponent, LegendComponent, CanvasRenderer])

interface ScoreItem {
  name: string
  score: number
  maxScore?: number
}

const props = defineProps<{
  scores: ScoreItem[]
  title?: string
}>()

const option = computed(() => {
  const indicators = props.scores.map(item => ({
    name: item.name,
    max: item.maxScore || 10
  }))
  
  const values = props.scores.map(item => item.score)
  
  return {
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#1f2937',
        fontSize: 12,
        fontWeight: 500
      },
      splitLine: {
        lineStyle: {
          color: ['#e5e7eb', '#d1d5db', '#9ca3af', '#6b7280', '#4b5563']
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(99, 102, 241, 0.02)', 'rgba(99, 102, 241, 0.04)', 
                  'rgba(99, 102, 241, 0.06)', 'rgba(99, 102, 241, 0.08)', 
                  'rgba(99, 102, 241, 0.1)']
        }
      },
      axisLine: {
        lineStyle: {
          color: '#d1d5db'
        }
      }
    },
    series: [{
      type: 'radar',
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: {
        width: 2,
        color: '#6366f1'
      },
      areaStyle: {
        color: 'rgba(99, 102, 241, 0.25)'
      },
      itemStyle: {
        color: '#6366f1',
        borderColor: '#fff',
        borderWidth: 2
      },
      data: [{
        value: values,
        name: props.title || '综合评分'
      }]
    }]
  }
})
</script>

<template>
  <div class="score-radar-chart">
    <h4 v-if="title" class="chart-title">{{ title }}</h4>
    <VChart :option="option" autoresize class="chart" />
  </div>
</template>

<style scoped>
.score-radar-chart {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px;
  text-align: center;
}

.chart {
  height: 300px;
  width: 100%;
}
</style>




