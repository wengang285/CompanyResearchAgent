import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { isAuthenticated } from './api/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('./views/LoginView.vue'),
    meta: { guest: true }  // 只允许未登录用户访问
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('./views/HomePage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/chat/:conversationId',
    name: 'Chat',
    component: () => import('./views/ChatView.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/research/:taskId',
    name: 'Research',
    component: () => import('./views/Research.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/report/:reportId',
    name: 'ReportDetail',
    component: () => import('./views/ReportDetail.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('./views/HistoryView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const authenticated = isAuthenticated()
  
  if (to.meta.requiresAuth && !authenticated) {
    // 需要登录但未登录，跳转登录页
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.guest && authenticated) {
    // 已登录用户访问登录页，跳转首页
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router



