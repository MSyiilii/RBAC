<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { coursesApi } from '../api/modules'
import { formatTime } from '../utils/format'
import { ReadOutlined } from '@ant-design/icons-vue'

const subscriptions = ref([])
const loading = ref(false)

const columns = [
  { title: '课程ID', dataIndex: 'course_id', width: 80 },
  { title: '课程名称', dataIndex: 'course_title' },
  { title: '课程类型', key: 'course_type', width: 120 },
  { title: 'Pro 权益', key: 'pro_info', width: 200 },
  { title: '报名时间', dataIndex: 'created_at', width: 180, customRender: ({ text }) => formatTime(text) },
  { title: '状态', key: 'status', width: 100 }
]

async function fetchSubscriptions() {
  loading.value = true
  try {
    const { data } = await coursesApi.mySubscriptions()
    subscriptions.value = Array.isArray(data) ? data : []
  } catch {
    message.error('获取订阅列表失败')
  } finally {
    loading.value = false
  }
}

function getStatusColor(status) {
  const map = { active: 'green', expired: 'red' }
  return map[status] || 'default'
}

function getStatusText(status) {
  const map = { active: '生效中', expired: '已过期' }
  return map[status] || status
}

onMounted(() => {
  fetchSubscriptions()
})
</script>

<template>
  <div>
    <a-page-header title="我的订阅" sub-title="查看已报名的课程及 Pro 权益">
      <template #extra>
        <a-button @click="fetchSubscriptions">刷新</a-button>
      </template>
    </a-page-header>

    <a-card :bordered="false">
      <a-empty v-if="!loading && subscriptions.length === 0" description="暂无订阅课程">
        <template #image>
          <ReadOutlined style="font-size: 64px; color: #ccc" />
        </template>
      </a-empty>

      <a-table
        v-else
        :columns="columns"
        :data-source="subscriptions"
        :loading="loading"
        :row-key="(r) => r.id"
        :pagination="{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'course_type'">
            <a-tag :color="record.course_type === 'online' ? 'blue' : 'orange'">
              {{ record.course_type === 'online' ? '线上课' : '线下课' }}
            </a-tag>
          </template>

          <template v-if="column.key === 'pro_info'">
            <span v-if="record.course_type === 'offline'">
              <a-tag color="gold">终身 Pro</a-tag>
            </span>
            <span v-else-if="record.pro_expires_at">
              <a-tag color="blue">Pro 到期: {{ formatTime(record.pro_expires_at) }}</a-tag>
            </span>
            <span v-else>
              <a-tag>一年 Pro</a-tag>
            </span>
          </template>

          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>
