<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import {
  DashboardOutlined,
  UserOutlined,
  SafetyOutlined,
  LockOutlined,
  AppstoreOutlined,
  ReadOutlined,
  StarOutlined,
  GiftOutlined,
  TrophyOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const collapsed = ref(false)
const selectedKeys = ref([])

const isLoginPage = computed(() => route.path === '/')

const menuItems = computed(() => {
  const items = [
    { key: '/dashboard', icon: 'DashboardOutlined', label: '仪表盘', show: true },
    { key: '/users', icon: 'UserOutlined', label: '用户管理', show: auth.isAdmin },
    { key: '/roles', icon: 'SafetyOutlined', label: '角色管理', show: auth.isAdmin },
    { key: '/permissions', icon: 'LockOutlined', label: '权限管理', show: auth.isAdmin },
    { key: '/features', icon: 'AppstoreOutlined', label: '功能管理', show: auth.isAdmin },
    { key: '/courses', icon: 'ReadOutlined', label: '课程管理', show: true },
    { key: '/courses/my', icon: 'StarOutlined', label: '我的订阅', show: true },
    { key: '/points', icon: 'TrophyOutlined', label: '积分中心', show: true },
    { key: '/entitlements', icon: 'GiftOutlined', label: '权益管理', show: true }
  ]
  return items.filter((item) => item.show)
})

watch(
  () => route.path,
  (path) => {
    selectedKeys.value = [path]
  },
  { immediate: true }
)

onMounted(() => {
  if (auth.isLoggedIn) {
    auth.fetchMe()
  }
})

function onMenuClick({ key }) {
  router.push(key)
}
</script>

<template>
  <div v-if="isLoginPage">
    <router-view />
  </div>

  <a-layout v-else style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible theme="dark" :width="220">
      <div class="logo">
        <span v-if="!collapsed">RBAC 管理系统</span>
        <span v-else>R</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="onMenuClick"
      >
        <a-menu-item v-for="item in menuItems" :key="item.key">
          <template #icon>
            <DashboardOutlined v-if="item.icon === 'DashboardOutlined'" />
            <UserOutlined v-if="item.icon === 'UserOutlined'" />
            <SafetyOutlined v-if="item.icon === 'SafetyOutlined'" />
            <LockOutlined v-if="item.icon === 'LockOutlined'" />
            <AppstoreOutlined v-if="item.icon === 'AppstoreOutlined'" />
            <ReadOutlined v-if="item.icon === 'ReadOutlined'" />
            <StarOutlined v-if="item.icon === 'StarOutlined'" />
            <TrophyOutlined v-if="item.icon === 'TrophyOutlined'" />
            <GiftOutlined v-if="item.icon === 'GiftOutlined'" />
          </template>
          <span>{{ item.label }}</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <a-layout-header class="app-header">
        <div class="header-left">
          <MenuFoldOutlined v-if="!collapsed" class="trigger" @click="collapsed = true" />
          <MenuUnfoldOutlined v-else class="trigger" @click="collapsed = false" />
        </div>
        <div class="header-right">
          <span class="username">
            <UserOutlined style="color: white;" /> <span style="color: white;">{{ auth.username }}</span>
          </span>
          <a-button type="link" danger @click="auth.logout()">
            <template #icon><LogoutOutlined /></template>
            退出登录
          </a-button>
        </div>
      </a-layout-header>

      <a-layout-content class="app-content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.08);
  margin: 0;
}

.app-header {
  background: #fff;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  height: 64px;
  line-height: 64px;
}

.header-left .trigger {
  font-size: 18px;
  cursor: pointer;
  transition: color 0.3s;
}

.header-left .trigger:hover {
  color: #1890ff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  font-size: 14px;
  color: #333;
}

.app-content {
  margin: 24px;
  padding: 24px;
  background: #f0f2f5;
  min-height: calc(100vh - 112px);
}
</style>
