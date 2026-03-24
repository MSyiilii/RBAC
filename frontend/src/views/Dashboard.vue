<script setup>
import { onMounted, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { pointsApi, entitlementsApi } from '../api/modules'
import { formatTime } from '../utils/format'
import {
  UserOutlined,
  SafetyOutlined,
  TrophyOutlined,
  GiftOutlined
} from '@ant-design/icons-vue'

const auth = useAuthStore()
const pointsBalance = ref(0)
const entitlements = ref([])

onMounted(async () => {
  await auth.fetchMe()
  try {
    const { data } = await pointsApi.balance()
    pointsBalance.value = data.balance || 0
  } catch { /* ignore */ }
  try {
    const { data } = await entitlementsApi.list()
    entitlements.value = (Array.isArray(data) ? data : []).filter(e => e.is_active)
  } catch { /* ignore */ }
})
</script>

<template>
  <div>
    <a-page-header title="仪表盘" sub-title="欢迎回来" />

    <a-row :gutter="[24, 24]">
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card hoverable>
          <a-statistic
            title="当前用户"
            :value="auth.username"
            style="text-align: center"
          >
            <template #prefix><UserOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>

      <a-col :xs="24" :sm="12" :lg="6">
        <a-card hoverable>
          <a-statistic
            title="角色数量"
            :value="auth.roles.length"
            style="text-align: center"
          >
            <template #prefix><SafetyOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>

      <a-col :xs="24" :sm="12" :lg="6">
        <a-card hoverable>
          <a-statistic
            title="积分余额"
            :value="pointsBalance"
            style="text-align: center"
          >
            <template #prefix><TrophyOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>

      <a-col :xs="24" :sm="12" :lg="6">
        <a-card hoverable>
          <a-statistic
            title="活跃权益"
            :value="entitlements.length"
            style="text-align: center"
          >
            <template #prefix><GiftOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[24, 24]" style="margin-top: 24px">
      <a-col :xs="24" :lg="12">
        <a-card title="当前角色" :bordered="false">
          <a-empty v-if="auth.roles.length === 0" description="暂无角色" />
          <div v-else>
            <a-tag
              v-for="role in auth.roles"
              :key="role.id"
              color="blue"
              style="margin-bottom: 8px; font-size: 14px; padding: 4px 12px"
            >
              {{ role.name }}
              <span v-if="role.description" style="margin-left: 4px">
                — {{ role.description }}
              </span>
            </a-tag>
          </div>
        </a-card>
      </a-col>

      <a-col :xs="24" :lg="12">
        <a-card title="活跃权益" :bordered="false">
          <a-empty v-if="entitlements.length === 0" description="暂无权益" />
          <a-list v-else :data-source="entitlements" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <GiftOutlined /> {{ item.feature_key }}
                  </template>
                  <template #description>
                    来源: {{ item.source }}
                    <span v-if="item.expires_at"> | 到期: {{ formatTime(item.expires_at) }}</span>
                    <span v-else> | 永久</span>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>
