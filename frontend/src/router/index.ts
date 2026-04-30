import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/indicators',
      name: 'Indicators',
      component: () => import('../views/Indicators.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/evaluation',
      name: 'Evaluation',
      component: () => import('../views/Evaluation.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/simulation',
      name: 'Simulation',
      component: () => import('../views/Simulation.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/benchmark',
      name: 'Benchmark',
      component: () => import('../views/Benchmark.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('../views/ChatAssistant.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/Profile.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'Admin',
      component: () => import('../views/Admin.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('cgdss_token')
  const userStr = localStorage.getItem('cgdss_user')

  // 不需要登录的页面
  if (to.meta.requiresAuth === false) {
    if (token && to.path === '/login') {
      next('/dashboard')
    } else {
      next()
    }
    return
  }

  // 需要登录的页面
  if (!token) {
    next('/login')
    return
  }

  // 需要管理员权限的页面
  if (to.meta.requiresAdmin) {
    try {
      const user = JSON.parse(userStr || '{}')
      if (user.role !== 'admin') {
        next('/dashboard')
        return
      }
    } catch (e) {
      next('/login')
      return
    }
  }

  next()
})

export default router
