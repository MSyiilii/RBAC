import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../views/Users.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/roles',
    name: 'Roles',
    component: () => import('../views/Roles.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/permissions',
    name: 'Permissions',
    component: () => import('../views/Permissions.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/features',
    name: 'Features',
    component: () => import('../views/Features.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/courses',
    name: 'Courses',
    component: () => import('../views/Courses.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/courses/my',
    name: 'MySubscriptions',
    component: () => import('../views/MySubscriptions.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/points',
    name: 'Points',
    component: () => import('../views/Points.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/entitlements',
    name: 'Entitlements',
    component: () => import('../views/Entitlements.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    next({ path: '/' })
  } else if (to.meta.guest && token) {
    next({ path: '/dashboard' })
  } else {
    next()
  }
})

export default router
