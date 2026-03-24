import axios from 'axios'
import { message } from 'ant-design-vue'
import { authApi } from './modules'
import router from '../router'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

let isRefreshing = false
let pendingQueue = []

function onRefreshed(newToken) {
  pendingQueue.forEach((cb) => cb(newToken))
  pendingQueue = []
}

function onRefreshFailed() {
  pendingQueue.forEach((cb) => cb(null))
  pendingQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes('/auth/login') &&
      !originalRequest.url.includes('/auth/refresh')
    ) {
      originalRequest._retry = true

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingQueue.push((newToken) => {
            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
              resolve(api(originalRequest))
            } else {
              reject(error)
            }
          })
        })
      }

      isRefreshing = true
      const refreshToken = localStorage.getItem('refreshToken')

      if (!refreshToken) {
        isRefreshing = false
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('user')
        message.error('登录已过期，请重新登录')
        router.push('/')
        return Promise.reject(error)
      }

      try {
        const { data } = await authApi.refresh({ refresh_token: refreshToken })
        const newToken = data.access_token
        localStorage.setItem('token', newToken)
        localStorage.setItem('refreshToken', data.refresh_token) 

        isRefreshing = false
        onRefreshed(newToken)

        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      } catch {
        isRefreshing = false
        onRefreshFailed()
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('user')
        message.error('登录已过期，请重新登录')
        router.push('/')
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

export default api
