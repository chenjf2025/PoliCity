import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue')
    },
    {
      path: '/indicators',
      name: 'Indicators',
      component: () => import('../views/Indicators.vue')
    },
    {
      path: '/evaluation',
      name: 'Evaluation',
      component: () => import('../views/Evaluation.vue')
    },
    {
      path: '/simulation',
      name: 'Simulation',
      component: () => import('../views/Simulation.vue')
    },
    {
      path: '/benchmark',
      name: 'Benchmark',
      component: () => import('../views/Benchmark.vue')
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('../views/ChatAssistant.vue')
    }
  ]
})

export default router
