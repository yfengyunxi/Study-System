import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import Chat from '../views/Chat.vue'
import Dashboard from '../views/Dashboard.vue'
import Login from '../views/Login.vue'
import MaterialDetail from '../views/MaterialDetail.vue'
import Materials from '../views/Materials.vue'
import Plans from '../views/Plans.vue'
import Profile from '../views/Profile.vue'
import Register from '../views/Register.vue'

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
