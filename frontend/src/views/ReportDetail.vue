<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { reportApi } from '@/api/research'
import ReportViewer from '@/components/ReportViewer.vue'
import type { Report } from '@/types'

const props = defineProps<{
  reportId: string
}>()

const router = useRouter()
const report = ref<Report | null>(null)
const isLoading = ref(true)

onMounted(async () => {
  try {
    const data = await reportApi.getReport(props.reportId)
    report.value = data
  } catch {
    ElMessage.error('获取报告详情失败')
  } finally {
    isLoading.value = false
  }
})

function goBack() {
  router.push('/')
}
</script>

<template>
  <div class="report-detail-page">
    <div class="page-header">
      <el-button @click="goBack" :icon="ArrowLeft" text>
        返回首页
      </el-button>
    </div>

    <div v-if="isLoading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </div>

    <ReportViewer
      v-else-if="report"
      :report="report.content || report"
      :task-id="report.task_id || ''"
    />

    <el-empty v-else description="报告不存在" />
  </div>
</template>

<style scoped>
.report-detail-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.loading-state {
  padding: 40px;
  background: white;
  border-radius: 12px;
}
</style>





