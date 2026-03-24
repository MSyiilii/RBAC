import { defineStore } from 'pinia'
import { authApi } from '../api/modules'
import { message } from 'ant-design-vue'
import router from '../router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: localStorage.getItem('token') || null,
    refreshToken: localStorage.getItem('refreshToken') || null
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    username: (state) => state.user?.username || '',
    roles: (state) => state.user?.roles || [],
    permissions() {
      const perms = new Set()
      for (const role of this.roles) {
        for (const p of role.permissions || []) {
          perms.add(p.key)
        }
      }
      return [...perms]
    }
  },

  actions: {
    hasPermission(key) {
      return this.permissions.includes(key)
    },

    hasAnyPermission(keys) {
      return keys.some((k) => this.permissions.includes(k))
    },

    async login(credentials) {
      try {
        const { data } = await authApi.login(credentials)
        this.token = data.access_token
        this.refreshToken = data.refresh_token
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('refreshToken', data.refresh_token)
        await this.fetchMe()
        message.success('登录成功')
        router.push('/dashboard')
      } catch (error) {
        const msg = error.response?.data?.detail || '登录失败，请检查用户名和密码'
        message.error(msg)
        throw error
      }
    },

    async fetchMe() {
      try {
        const { data } = await authApi.me()
        this.user = data
        localStorage.setItem('user', JSON.stringify(data))
      } catch {
        // silently fail
      }
    },

    async doRefreshToken() {
      try {
        const { data } = await authApi.refresh({ refresh_token: this.refreshToken })
        this.token = data.access_token
        this.refreshToken = data.refresh_token
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('refreshToken', data.refresh_token)
      } catch {
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.refreshToken = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
      router.push('/')
      message.success('已退出登录')
    }
  }
})
