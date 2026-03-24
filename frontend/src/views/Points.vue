<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { pointsApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'
import { formatTime } from '../utils/format'

const auth = useAuthStore()
import {
  TrophyOutlined,
  CalendarOutlined,
  UserAddOutlined,
  ReadOutlined,
  CommentOutlined,
  UnlockOutlined
} from '@ant-design/icons-vue'

const balance = ref(0)
const ledger = ref([])
const unlockRules = ref([])
const loading = ref(false)
const rulesLoading = ref(false)

const earnActions = [
  { key: 'daily_checkin', label: '每日签到', icon: 'CalendarOutlined', points: '+10' },
  { key: 'invite_friend', label: '邀请好友', icon: 'UserAddOutlined', points: '+50' },
  { key: 'complete_course', label: '完成课程', icon: 'ReadOutlined', points: '+100' },
  { key: 'community_interact', label: '社区互动', icon: 'CommentOutlined', points: '+5' }
]

const ledgerColumns = [
  { title: '时间', dataIndex: 'created_at', width: 180, customRender: ({ text }) => formatTime(text) },
  { title: '积分变动', key: 'change' },
  { title: '余额', dataIndex: 'balance_after' },
  { title: '描述', dataIndex: 'reason' }
]

async function fetchBalance() {
  try {
    const { data } = await pointsApi.balance()
    balance.value = data.balance || 0
  } catch {
    // ignore
  }
}

async function fetchLedger() {
  loading.value = true
  try {
    const { data } = await pointsApi.ledger()
    ledger.value = Array.isArray(data) ? data : data.items || []
  } catch {
    message.error('获取积分记录失败')
  } finally {
    loading.value = false
  }
}

async function fetchUnlockRules() {
  rulesLoading.value = true
  try {
    const { data } = await pointsApi.unlockRules()
    unlockRules.value = Array.isArray(data) ? data : data.items || []
  } catch {
    // ignore
  } finally {
    rulesLoading.value = false
  }
}

async function handleEarn(actionKey) {
  try {
    await pointsApi.earn({ action_key: actionKey })
    message.success('积分获取成功！')
    fetchBalance()
    fetchLedger()
  } catch (err) {
    message.error(err.response?.data?.detail || '操作失败')
  }
}

async function handleUnlock(featureKey) {
  try {
    await pointsApi.unlock(featureKey)
    message.success('解锁成功！')
    fetchBalance()
    fetchLedger()
    fetchUnlockRules()
  } catch (err) {
    message.error(err.response?.data?.detail || '解锁失败')
  }
}

onMounted(() => {
  fetchBalance()
  fetchLedger()
  fetchUnlockRules()
})
</script>

<template>
  <div>
    <a-page-header title="积分中心" sub-title="赚取积分，解锁高级功能" />

    <a-row :gutter="[24, 24]">
      <a-col :xs="24" :lg="8">
        <a-card :bordered="false">
          <a-statistic
            title="积分余额"
            :value="balance"
            :value-style="{ color: '#faad14', fontSize: '36px' }"
            style="text-align: center"
          >
            <template #prefix><TrophyOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>

      <a-col :xs="24" :lg="16">
        <a-card title="赚取积分" :bordered="false">
          <a-row :gutter="[12, 12]">
            <a-col v-for="action in earnActions" :key="action.key" :xs="12" :sm="6">
              <a-button
                block
                size="large"
                style="height: auto; padding: 16px 8px"
                @click="handleEarn(action.key)"
              >
                <div style="text-align: center">
                  <CalendarOutlined v-if="action.icon === 'CalendarOutlined'" style="font-size: 24px; display: block; margin-bottom: 8px" />
                  <UserAddOutlined v-if="action.icon === 'UserAddOutlined'" style="font-size: 24px; display: block; margin-bottom: 8px" />
                  <ReadOutlined v-if="action.icon === 'ReadOutlined'" style="font-size: 24px; display: block; margin-bottom: 8px" />
                  <CommentOutlined v-if="action.icon === 'CommentOutlined'" style="font-size: 24px; display: block; margin-bottom: 8px" />
                  <div>{{ action.label }}</div>
                  <div style="color: #52c41a; font-weight: bold">{{ action.points }}</div>
                </div>
              </a-button>
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[24, 24]" style="margin-top: 24px">
      <a-col :xs="24" :lg="16">
        <a-card title="积分流水" :bordered="false">
          <a-table
            :columns="ledgerColumns"
            :data-source="ledger"
            :loading="loading"
            :row-key="(r) => r.id"
            :pagination="{ pageSize: 8, showTotal: (t) => `共 ${t} 条` }"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'change'">
                <span :style="{ color: record.change > 0 ? '#52c41a' : '#f5222d', fontWeight: 'bold' }">
                  {{ record.change > 0 ? '+' : '' }}{{ record.change }}
                </span>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>

      <a-col :xs="24" :lg="8">
        <a-card title="积分解锁规则" :bordered="false" :loading="rulesLoading">
          <a-empty v-if="unlockRules.length === 0" description="暂无解锁规则" />
          <a-list v-else :data-source="unlockRules" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <UnlockOutlined /> {{ item.feature_key }}
                  </template>
                  <template #description>
                    需要 {{ item.required_points }} 积分
                    <span v-if="item.trial_days">（试用 {{ item.trial_days }} 天）</span>
                  </template>
                </a-list-item-meta>
                <template #actions>
                  <a-button
                    type="primary"
                    size="small"
                    :disabled="balance < item.required_points"
                    @click="handleUnlock(item.feature_key)"
                  >
                    解锁
                  </a-button>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>
