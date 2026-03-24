<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { entitlementsApi, featuresApi, usersApi } from '../api/modules'
import { formatTime } from '../utils/format'
import { useAuthStore } from '../stores/auth'
import { PlusOutlined, DeleteOutlined, CheckCircleOutlined, SearchOutlined } from '@ant-design/icons-vue'

const auth = useAuthStore()
const entitlements = ref([])
const allFeatures = ref([])
const allUsers = ref([])
const loading = ref(false)
const grantModalVisible = ref(false)
const checkUserId = ref(null)

const grantForm = reactive({
  user_id: null,
  feature_key: '',
  source: 'admin',
  expires_at: null
})

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '用户ID', dataIndex: 'user_id', width: 80 },
  { title: '功能', dataIndex: 'feature_key' },
  { title: '来源', key: 'source' },
  { title: '授予时间', dataIndex: 'granted_at', width: 180, customRender: ({ text }) => formatTime(text) },
  { title: '到期时间', dataIndex: 'expires_at', width: 180, customRender: ({ text }) => formatTime(text) },
  { title: '状态', key: 'status' },
  { title: '操作', key: 'action', width: 100 }
]

function getSourceText(source) {
  const map = { admin: '管理员开通', course: '购买课程', points: '积分兑换', trial: '试用' }
  return map[source] || source
}

async function fetchEntitlements() {
  loading.value = true
  try {
    const { data } = await entitlementsApi.list()
    entitlements.value = Array.isArray(data) ? data : []
  } catch {
    message.error('获取权益列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchFeatures() {
  try {
    const { data } = await featuresApi.list()
    allFeatures.value = Array.isArray(data) ? data : []
  } catch { /* ignore */ }
}

async function fetchUsers() {
  try {
    const { data } = await usersApi.list()
    allUsers.value = Array.isArray(data) ? data : []
  } catch { /* ignore */ }
}

function openGrantModal() {
  grantForm.user_id = null
  grantForm.feature_key = ''
  grantForm.source = 'admin'
  grantForm.expires_at = null
  grantModalVisible.value = true
}

async function handleGrant() {
  try {
    const payload = {
      user_id: grantForm.user_id,
      feature_key: grantForm.feature_key,
      source: grantForm.source
    }
    if (grantForm.expires_at) payload.expires_at = grantForm.expires_at
    await entitlementsApi.grant(payload)
    message.success('权益授予成功')
    grantModalVisible.value = false
    fetchEntitlements()
  } catch (err) {
    message.error(err.response?.data?.detail || '授予失败')
  }
}

async function handleRevoke(record) {
  try {
    await entitlementsApi.revoke(record.id)
    message.success('权益撤销成功')
    fetchEntitlements()
  } catch (err) {
    message.error(err.response?.data?.detail || '撤销失败')
  }
}


async function handleCheckFeature() {
  const uid = checkUserId.value || auth.user?.id
  if (!uid) {
    message.warning('请选择用户')
    return
  }
  const { data } = await entitlementsApi.getList(uid)
  entitlements.value = Array.isArray(data) ? data : []
}

onMounted(() => {
  fetchEntitlements()
  if (auth.hasPermission('entitlement:grant')) {
    fetchFeatures()
    fetchUsers()
  }
})
</script>

<template>
  <div>
    <a-page-header title="权益管理" sub-title="管理功能权益的授予与查看">
      <template #extra>
        <a-button v-if="auth.hasPermission('entitlement:grant')" type="primary" @click="openGrantModal">
          <template #icon>
            <PlusOutlined />
          </template>
          授予权益
        </a-button>
      </template>
    </a-page-header>

    <a-card title="功能权限搜索" :bordered="false" style="margin-bottom: 24px" v-if="auth.hasPermission('entitlement:grant')">
      <a-space wrap>
        <a-select v-if="auth.hasPermission('entitlement:grant')" v-model:value="checkUserId" placeholder="选择用户"
          allow-clear show-search
          :filter-option="(input, option) => option.label.toLowerCase().includes(input.toLowerCase())"
          :options="allUsers.map((u) => ({ value: u.id, label: u.username }))" style="width: 200px" />
        <a-button type="primary" @click="handleCheckFeature">
          <template #icon>
            <SearchOutlined />
          </template>
          搜索权益
        </a-button>
      </a-space>
    </a-card>

    <a-card title="权益列表" :bordered="false">
      <a-table :columns="columns" :data-source="entitlements" :loading="loading" :row-key="(r) => r.id"
        :pagination="{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'source'">
            <a-tag>{{ getSourceText(record.source) }}</a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="record.is_active ? 'green' : 'red'">
              <CheckCircleOutlined v-if="record.is_active" />
              {{ record.is_active ? '生效中' : '已失效' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-popconfirm v-if="auth.hasPermission('entitlement:revoke')" title="确定要撤销该权益吗？"
              @confirm="handleRevoke(record)">
              <a-button size="small" danger>
                <template #icon>
                  <DeleteOutlined />
                </template>
                撤销
              </a-button>
            </a-popconfirm>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:open="grantModalVisible" title="授予权益" @ok="handleGrant" :destroyOnClose="true">
      <a-form layout="vertical">
        <a-form-item label="选择用户" required>
          <a-select v-model:value="grantForm.user_id" placeholder="请选择用户" show-search
            :filter-option="(input, option) => option.label.toLowerCase().includes(input.toLowerCase())"
            :options="allUsers.map((u) => ({ value: u.id, label: u.username }))" />
        </a-form-item>
        <a-form-item label="功能代码" required>
          <a-select v-model:value="grantForm.feature_key" placeholder="请选择功能" show-search
            :options="allFeatures.map((f) => ({ value: f.key, label: f.name + ' (' + f.key + ')' }))" />
        </a-form-item>
        <a-form-item label="来源">
          <a-select v-model:value="grantForm.source">
            <a-select-option value="admin">管理员开通</a-select-option>
            <a-select-option value="course">购买课程</a-select-option>
            <a-select-option value="points">积分兑换</a-select-option>
            <a-select-option value="trial">试用</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="到期时间">
          <a-date-picker v-model:value="grantForm.expires_at" show-time placeholder="留空为永久" style="width: 100%"
            value-format="YYYY-MM-DDTHH:mm:ss" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>
