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
    meta: { requiresAuth: true, requiredPermission: 'user:read' }
  },
  {
    path: '/roles',
    name: 'Roles',
    component: () => import('../views/Roles.vue'),
    meta: { requiresAuth: true, requiredPermission: 'role:read' }
  },
  {
    path: '/permissions',
    name: 'Permissions',
    component: () => import('../views/Permissions.vue'),
    meta: { requiresAuth: true, requiredPermission: 'permission:read' }
  },
  {
    path: '/features',
    name: 'Features',
    component: () => import('../views/Features.vue'),
    meta: { requiresAuth: true, requiredPermission: 'feature:read' }
  },
  {
    path: '/courses',
    name: 'Courses',
    component: () => import('../views/Courses.vue'),
    meta: { requiresAuth: true, requiredPermission: 'course:read' }
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
    meta: { requiresAuth: true, requiredPermission: 'points:read' }
  },
  {
    path: '/entitlements',
    name: 'Entitlements',
    component: () => import('../views/Entitlements.vue'),
    meta: { requiresAuth: true, requiredPermission: 'entitlement:read' }
  }
]

function getUserPermissions() {
  try {
    const user = JSON.parse(localStorage.getItem('user') || 'null')
    if (!user || !user.roles) return []
    const perms = new Set()
    for (const role of user.roles) {
      for (const p of role.permissions || []) {
        perms.add(p.key)
      }
    }
    return [...perms]
  } catch {
    return []
  }
}

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
  } else if (to.meta.requiredPermission) {
    const perms = getUserPermissions()
    if (!perms.includes(to.meta.requiredPermission)) {
      next({ path: '/dashboard' })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
