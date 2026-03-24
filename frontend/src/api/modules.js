import api from './index'

export const authApi = {
  login(data) {
    return api.post('/api/auth/login', data)
  },
  me() {
    return api.get('/api/auth/me')
  },
  refresh(data) {
    return api.post('/api/auth/refresh', data)
  }
}

export const usersApi = {
  list() {
    return api.get('/api/users')
  },
  get(id) {
    return api.get(`/api/users/${id}`)
  },
  create(data) {
    return api.post('/api/users', data)
  },
  update(id, data) {
    return api.put(`/api/users/${id}`, data)
  },
  delete(id) {
    return api.delete(`/api/users/${id}`)
  },
  getRoles(userId) {
    return api.get(`/api/users/${userId}/roles`)
  },
  assignRole(userId, roleId) {
    return api.post(`/api/users/${userId}/roles`, { role_id: roleId })
  },
  revokeRole(userId, roleId) {
    return api.delete(`/api/users/${userId}/roles/${roleId}`)
  }
}

export const rolesApi = {
  list() {
    return api.get('/api/roles')
  },
  get(id) {
    return api.get(`/api/roles/${id}`)
  },
  create(data) {
    return api.post('/api/roles', data)
  },
  update(id, data) {
    return api.put(`/api/roles/${id}`, data)
  },
  delete(id) {
    return api.delete(`/api/roles/${id}`)
  },
  getPermissions(roleId) {
    return api.get(`/api/roles/${roleId}/permissions`)
  },
  assignPermission(roleId, permissionId) {
    return api.post(`/api/roles/${roleId}/permissions`, { permission_id: permissionId })
  },
  revokePermission(roleId, permissionId) {
    return api.delete(`/api/roles/${roleId}/permissions/${permissionId}`)
  }
}

export const permissionsApi = {
  list() {
    return api.get('/api/permissions')
  },
  create(data) {
    return api.post('/api/permissions', data)
  },
  update(id, data) {
    return api.put(`/api/permissions/${id}`, data)
  },
  delete(id) {
    return api.delete(`/api/permissions/${id}`)
  }
}

export const featuresApi = {
  list() {
    return api.get('/api/features')
  },
  get(id) {
    return api.get(`/api/features/${id}`)
  },
  create(data) {
    return api.post('/api/features', data)
  },
  update(id, data) {
    return api.put(`/api/features/${id}`, data)
  },
  delete(id) {
    return api.delete(`/api/features/${id}`)
  }
}

export const featurePackagesApi = {
  list() {
    return api.get('/api/feature-packages')
  },
  get(id) {
    return api.get(`/api/feature-packages/${id}`)
  },
  create(data) {
    return api.post('/api/feature-packages', data)
  },
  update(id, data) {
    return api.put(`/api/feature-packages/${id}`, data)
  },
  delete(id) {
    return api.delete(`/api/feature-packages/${id}`)
  }
}

export const coursesApi = {
  list() {
    return api.get('/api/courses')
  },
  get(id) {
    return api.get(`/api/courses/${id}`)
  },
  create(data) {
    return api.post('/api/courses', data)
  },
  update(id, data) {
    return api.put(`/api/courses/${id}`, data)
  },
  delete(id) {
    return api.delete(`/api/courses/${id}`)
  },
  subscribe(courseId) {
    return api.post(`/api/courses/${courseId}/subscribe`)
  },
  subscribers(courseId) {
    return api.get(`/api/courses/${courseId}/subscribers`)
  },
  mySubscriptions() {
    return api.get('/api/my/subscriptions')
  },
  expireCheck() {
    return api.post('/api/courses/expire-check')
  }
}

export const pointsApi = {
  balance() {
    return api.get('/api/points/balance')
  },
  ledger() {
    return api.get('/api/points/ledger')
  },
  earn(data) {
    return api.post('/api/points/earn', data)
  },
  rules() {
    return api.get('/api/points/rules')
  },
  createRule(data) {
    return api.post('/api/points/rules', data)
  },
  unlockRules() {
    return api.get('/api/points/unlock-rules')
  },
  createUnlockRule(data) {
    return api.post('/api/points/unlock-rules', data)
  },
  checkUnlock(featureKey) {
    return api.get(`/api/points/unlock-check/${featureKey}`)
  },
  unlock(featureKey) {
    return api.post(`/api/points/unlock/${featureKey}`)
  }
}

export const entitlementsApi = {
  list() {
    return api.get('/api/entitlements')
  },
  check(data) {
    return api.post('/api/entitlements/check', data)
  },
  grant(data) {
    return api.post('/api/entitlements/grant', data)
  },
  revoke(id) {
    return api.post(`/api/entitlements/revoke/${id}`)
  },
  expireStale() {
    return api.post('/api/entitlements/expire-stale')
  }
}
