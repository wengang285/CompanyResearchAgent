<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterView, useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { isAuthenticated, getStoredUser, authApi, type User } from '@/api/auth'

const router = useRouter()
const route = useRoute()

const user = ref<User | null>(null)

// 是否显示 header（登录页不显示）
const showHeader = computed(() => route.name !== 'Login')

// 检查登录状态
onMounted(() => {
  if (isAuthenticated()) {
    user.value = getStoredUser()
  }
})

// 登出
async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出登录', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await authApi.logout()
    user.value = null
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<template>
  <div class="app-container">
    <header v-if="showHeader" class="app-header">
      <div class="header-content">
        <router-link to="/" class="logo">
          <el-icon :size="28"><DataAnalysis /></el-icon>
          <span class="logo-text">上市公司深度研究</span>
        </router-link>
        <nav class="nav-links">
          <router-link to="/" class="nav-link">首页</router-link>
          <router-link to="/history" class="nav-link">历史</router-link>
        </nav>
        <div v-if="user" class="user-section">
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-avatar :size="32">{{ user.username.charAt(0).toUpperCase() }}</el-avatar>
              <span class="username">{{ user.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <el-icon><User /></el-icon>
                  {{ user.username }}
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>
    <main :class="['app-main', { 'no-header': !showHeader }]">
      <RouterView />
    </main>
    <footer v-if="showHeader" class="app-footer">
      <p>AI Agent 驱动的智能研究系统 © 2025</p>
    </footer>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --primary-color: #1a1a2e;
  --secondary-color: #16213e;
  --accent-color: #0f3460;
  --highlight-color: #e94560;
  --bg-color: #f8fafc;
  --text-color: #1e293b;
  --text-light: #64748b;
  --card-bg: #ffffff;
  --border-color: #e2e8f0;
}

body {
  font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-color);
  color: var(--text-color);
  min-height: 100vh;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
  padding: 0 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: white;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-link {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  font-size: 15px;
  transition: color 0.2s;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: white;
}

.user-section {
  margin-left: auto;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 20px;
  transition: background 0.2s;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.1);
}

.username {
  font-size: 14px;
}

.app-main {
  flex: 1;
  padding: 32px 24px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.app-main.no-header {
  padding: 0;
  max-width: none;
}

.app-footer {
  background: var(--primary-color);
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  padding: 20px;
  font-size: 14px;
}
</style>



