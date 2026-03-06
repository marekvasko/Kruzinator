import { createRouter, createWebHistory } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'

const ConsentView = () => import('@/views/ConsentView.vue')
const UserView = () => import('@/views/UserView.vue')
const CaptureView = () => import('@/views/CaptureView.vue')
const ReviewView = () => import('@/views/ReviewView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      redirect: () => {
        const workflow = useWorkflowStore()
        if (!workflow.consented) return { name: 'consent' }
        if (!workflow.userId) return { name: 'user' }
        return { name: 'capture' }
      },
    },
    { path: '/consent', name: 'consent', component: ConsentView },
    { path: '/user', name: 'user', component: UserView },
    { path: '/capture', name: 'capture', component: CaptureView },
    { path: '/review', name: 'review', component: ReviewView },
  ],
})

router.beforeEach((to) => {
  const workflow = useWorkflowStore()

  if (to.name !== 'consent' && !workflow.consented) return { name: 'consent' }
  if ((to.name === 'capture' || to.name === 'review') && !workflow.userId) return { name: 'user' }
  return true
})

export default router
