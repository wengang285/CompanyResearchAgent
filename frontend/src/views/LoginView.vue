<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'

const router = useRouter()

// 状态
const isLogin = ref(true)  // true: 登录, false: 注册
const isLoading = ref(false)

// 表单数据
const form = ref({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

// 表单验证
const isFormValid = computed(() => {
  if (isLogin.value) {
    return form.value.username.trim() && form.value.password.trim()
  } else {
    return (
      form.value.username.trim() &&
      form.value.password.trim() &&
      form.value.password === form.value.confirmPassword &&
      form.value.password.length >= 6
    )
  }
})

// 切换登录/注册
function toggleMode() {
  isLogin.value = !isLogin.value
  form.value = {
    username: '',
    password: '',
    confirmPassword: '',
    email: ''
  }
}

// 提交表单
async function handleSubmit() {
  if (!isFormValid.value || isLoading.value) return
  
  isLoading.value = true
  try {
    if (isLogin.value) {
      await authApi.login(form.value.username, form.value.password)
      ElMessage.success('登录成功')
    } else {
      await authApi.register(
        form.value.username,
        form.value.password,
        form.value.email || undefined
      )
      ElMessage.success('注册成功')
    }
    
    // 跳转到首页
    router.push('/')
  } catch (e: any) {
    const message = e.response?.data?.detail || '操作失败，请重试'
    ElMessage.error(message)
  } finally {
    isLoading.value = false
  }
}

// 回车提交
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && isFormValid.value) {
    handleSubmit()
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 左侧装饰 -->
      <div class="login-banner">
        <div class="banner-content">
          <h1 class="banner-title">🤖 AI Research Agent</h1>
          <p class="banner-subtitle">智能上市公司深度研究系统</p>
          <div class="banner-features">
            <div class="feature-item">
              <span class="feature-icon">📊</span>
              <span>多 Agent 协作分析</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📈</span>
              <span>专业财务与市场分析</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📝</span>
              <span>自动生成研究报告</span>
            </div>
          </div>
        </div>
        <div class="banner-decoration">
          <div class="deco-circle c1"></div>
          <div class="deco-circle c2"></div>
          <div class="deco-circle c3"></div>
        </div>
      </div>
      
      <!-- 右侧表单 -->
      <div class="login-form-wrapper">
        <div class="form-header">
          <h2>{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
          <p>{{ isLogin ? '登录以继续使用' : '注册一个新账号' }}</p>
        </div>
        
        <form class="login-form" @submit.prevent="handleSubmit" @keydown="handleKeydown">
          <div class="form-group">
            <label>用户名</label>
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="User"
            />
          </div>
          
          <div v-if="!isLogin" class="form-group">
            <label>邮箱（可选）</label>
            <el-input
              v-model="form.email"
              placeholder="请输入邮箱"
              size="large"
              type="email"
              :prefix-icon="Message"
            />
          </div>
          
          <div class="form-group">
            <label>密码</label>
            <el-input
              v-model="form.password"
              placeholder="请输入密码"
              size="large"
              type="password"
              show-password
              :prefix-icon="Lock"
            />
            <span v-if="!isLogin && form.password && form.password.length < 6" class="hint error">
              密码至少 6 位
            </span>
          </div>
          
          <div v-if="!isLogin" class="form-group">
            <label>确认密码</label>
            <el-input
              v-model="form.confirmPassword"
              placeholder="请再次输入密码"
              size="large"
              type="password"
              show-password
              :prefix-icon="Lock"
            />
            <span 
              v-if="form.confirmPassword && form.password !== form.confirmPassword" 
              class="hint error"
            >
              两次密码不一致
            </span>
          </div>
          
          <el-button
            type="primary"
            size="large"
            class="submit-btn"
            :loading="isLoading"
            :disabled="!isFormValid"
            @click="handleSubmit"
          >
            {{ isLogin ? '登 录' : '注 册' }}
          </el-button>
        </form>
        
        <div class="form-footer">
          <span>{{ isLogin ? '还没有账号？' : '已有账号？' }}</span>
          <a href="#" @click.prevent="toggleMode">
            {{ isLogin ? '立即注册' : '去登录' }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { User, Lock, Message } from '@element-plus/icons-vue'
export default {
  components: { User, Lock, Message }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  display: flex;
  width: 100%;
  max-width: 900px;
  background: white;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* 左侧 Banner */
.login-banner {
  flex: 1;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.banner-content {
  position: relative;
  z-index: 1;
}

.banner-title {
  font-size: 28px;
  font-weight: 700;
  color: white;
  margin: 0 0 12px;
}

.banner-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 40px;
}

.banner-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
}

.feature-icon {
  font-size: 20px;
}

.banner-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.deco-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
}

.c1 {
  width: 200px;
  height: 200px;
  top: -50px;
  right: -50px;
}

.c2 {
  width: 150px;
  height: 150px;
  bottom: 50px;
  left: -30px;
}

.c3 {
  width: 100px;
  height: 100px;
  bottom: -20px;
  right: 50px;
}

/* 右侧表单 */
.login-form-wrapper {
  flex: 1;
  padding: 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.form-header {
  margin-bottom: 32px;
}

.form-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px;
}

.form-header p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.hint {
  font-size: 12px;
}

.hint.error {
  color: #ef4444;
}

.submit-btn {
  margin-top: 12px;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
}

.form-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.form-footer a {
  color: #6366f1;
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}

.form-footer a:hover {
  text-decoration: underline;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
    max-width: 400px;
  }
  
  .login-banner {
    padding: 32px;
  }
  
  .login-form-wrapper {
    padding: 32px;
  }
}
</style>




