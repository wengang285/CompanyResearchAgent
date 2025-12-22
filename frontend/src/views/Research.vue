<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useResearchStore } from '@/stores/research'
import ResearchProgress from '@/components/ResearchProgress.vue'
import ReportViewer from '@/components/ReportViewer.vue'

const props = defineProps<{
  taskId: string
}>()

const router = useRouter()
const store = useResearchStore()

const isLoadingResult = ref(false)

onMounted(async () => {
  try {
    // 获取任务状态
    await store.fetchTaskStatus(props.taskId)
    
    // 如果任务正在运行，开始状态同步
    if (store.currentTask?.status === 'running' || store.currentTask?.status === 'pending') {
      store.startStatusSync(props.taskId)
    }
    
    // 如果已完成，获取结果
    if (store.currentTask?.status === 'completed') {
      isLoadingResult.value = true
      await store.fetchTaskResult(props.taskId)
      isLoadingResult.value = false
    }
  } catch {
    ElMessage.error('获取任务信息失败')
  }
})

// 监听状态变化
watch(() => store.progress.status, async (newStatus, oldStatus) => {
  console.log(`状态变化: ${oldStatus} -> ${newStatus}`)
  
  if (newStatus === 'completed') {
    isLoadingResult.value = true
    try {
      await store.fetchTaskResult(props.taskId)
      ElMessage.success('研究完成！')
    } catch {
      ElMessage.error('获取研究结果失败')
    }
    isLoadingResult.value = false
  } else if (newStatus === 'failed') {
    ElMessage.error('研究失败')
  }
})

onUnmounted(() => {
  // 离开页面时停止同步
  store.stopStatusSync()
})

function goBack() {
  store.cleanup()
  router.push('/')
}
</script>

<template>
  <div class="research-page">
    <!-- 返回按钮 -->
    <div class="page-header">
      <el-button @click="goBack" :icon="ArrowLeft" text>
        返回首页
      </el-button>
      <h1 class="page-title" v-if="store.currentTask">
        {{ store.currentTask.company }} 研究分析
      </h1>
    </div>

    <!-- 加载状态 -->
    <div v-if="!store.currentTask" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 研究进行中 -->
    <template v-else-if="store.isResearching">
      <ResearchProgress
        :progress="store.progress"
        :company="store.currentTask.company"
      />
    </template>

    <!-- 研究失败 -->
    <template v-else-if="store.currentTask.status === 'failed'">
      <el-result
        icon="error"
        title="研究失败"
        :sub-title="store.currentTask.error_message || '发生未知错误'"
      >
        <template #extra>
          <el-button type="primary" @click="goBack">返回重试</el-button>
        </template>
      </el-result>
    </template>

    <!-- 研究完成 - 显示报告 -->
    <template v-else-if="store.currentTask.status === 'completed'">
      <div v-if="isLoadingResult" class="loading-result">
        <el-skeleton :rows="10" animated />
      </div>
      <ReportViewer
        v-else-if="store.currentTask.report_data"
        :report="store.currentTask.report_data"
        :task-id="taskId"
      />
      <el-empty v-else description="暂无报告数据" />
    </template>
  </div>
</template>

<style scoped>
.research-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
  margin: 0;
}

.loading-state,
.loading-result {
  padding: 40px;
  background: white;
  border-radius: 12px;
}
</style>
