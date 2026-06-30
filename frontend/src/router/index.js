import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const Chat = () => import('../views/Chat.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const Login = () => import('../views/Login.vue')
const MaterialDetail = () => import('../views/MaterialDetail.vue')
const Materials = () => import('../views/Materials.vue')
const Plans = () => import('../views/Plans.vue')
const Profile = () => import('../views/Profile.vue')
const Register = () => import('../views/Register.vue')

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', component: Login, meta: { public: true } },
  { path: '/register', component: Register, meta: { public: true } },
  { path: '/dashboard', component: Dashboard },
  { path: '/materials', component: Materials },
  { path: '/materials/:id', component: MaterialDetail },
  { path: '/chat', component: Chat },
  { path: '/plans', component: Plans },
  { path: '/plans/:id', component: Plans },
  { path: '/profile', component: Profile }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.token) {
    return '/login'
  }
  if (to.meta.public && auth.token) {
    return '/dashboard'
  }
  return true
})

export default router
