<script setup lang="ts">
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const emit = defineEmits<{
  start: [data: { company: string; depth: string; focus: string[] }]
}>()

defineProps<{
  loading?: boolean
}>()

const company = ref('')
const depth = ref('standard')
const focusAreas = ref<string[]>([])

const depthOptions = [
  { value: 'basic', label: '基础研究', desc: '快速了解公司概况' },
  { value: 'standard', label: '标准研究', desc: '全面分析财务和市场' },
  { value: 'deep', label: '深度研究', desc: '详尽分析，专业级报告' }
]

const focusOptions = [
  { value: 'financial', label: '财务分析' },
  { value: 'market', label: '市场地位' },
  { value: 'growth', label: '成长潜力' },
  { value: 'risk', label: '风险评估' },
  { value: 'valuation', label: '估值分析' }
]

function handleSubmit() {
  if (!company.value.trim()) {
    return
  }
  
  emit('start', {
    company: company.value.trim(),
    depth: depth.value,
    focus: focusAreas.value
  })
}
</script>

<template>
  <div class="company-input">
    <el-form @submit.prevent="handleSubmit" label-position="top">
      <!-- 公司名称输入 -->
      <el-form-item label="公司名称或股票代码">
        <el-input
          v-model="company"
          placeholder="请输入公司名称或股票代码，如: 贵州茅台、600519"
          size="large"
          clearable
          :prefix-icon="Search"
        />
      </el-form-item>

      <!-- 研究深度选择 -->
      <el-form-item label="研究深度">
        <el-radio-group v-model="depth" class="depth-group">
          <el-radio-button
            v-for="option in depthOptions"
            :key="option.value"
            :value="option.value"
          >
            <div class="depth-option">
              <span class="depth-label">{{ option.label }}</span>
              <span class="depth-desc">{{ option.desc }}</span>
            </div>
          </el-radio-button>
        </el-radio-group>
      </el-form-item>

      <!-- 关注重点 -->
      <el-form-item label="关注重点（可选）">
        <el-checkbox-group v-model="focusAreas" class="focus-group">
          <el-checkbox
            v-for="option in focusOptions"
            :key="option.value"
            :value="option.value"
            :label="option.label"
          />
        </el-checkbox-group>
      </el-form-item>

      <!-- 提交按钮 -->
      <el-form-item>
        <el-button
          type="primary"
          size="large"
          native-type="submit"
          :loading="loading"
          :disabled="!company.trim()"
          class="submit-btn"
        >
          <el-icon v-if="!loading"><Search /></el-icon>
          {{ loading ? '启动研究中...' : '开始研究' }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.company-input {
  padding: 10px 0;
}

.depth-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.depth-group :deep(.el-radio-button__inner) {
  border-radius: 8px !important;
  border: 1px solid var(--border-color) !important;
  padding: 12px 20px;
  height: auto;
}

.depth-group :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 8px !important;
}

.depth-group :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 8px !important;
}

.depth-group :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
  border-color: var(--primary-color) !important;
}

.depth-option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.depth-label {
  font-weight: 600;
}

.depth-desc {
  font-size: 12px;
  opacity: 0.8;
}

.focus-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.submit-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
  border: none;
  margin-top: 10px;
}

.submit-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%);
}
</style>





