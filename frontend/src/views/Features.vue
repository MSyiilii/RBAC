<script setup>
import { ref, reactive, onMounted, createVNode } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { featuresApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'
import { formatTime } from '../utils/format'
import { PlusOutlined, EditOutlined, DeleteOutlined, CrownOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue'

const auth = useAuthStore()

const features = ref([])
const loading = ref(false)
const modalVisible = ref(false)
const editingFeature = ref(null)

const form = reactive({
  key: '',
  name: '',
  description: '',
  is_pro: false
})

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '功能代码', dataIndex: 'key' },
  { title: '功能名称', dataIndex: 'name' },
  { title: '描述', dataIndex: 'description' },
  { title: '类型', key: 'type', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', width: 180, customRender: ({ text }) => formatTime(text) },
  { title: '操作', key: 'action', width: 200 }
]

async function fetchFeatures() {
  loading.value = true
  try {
    const { data } = await featuresApi.list()
    features.value = Array.isArray(data) ? data : []
  } catch {
    message.error('获取功能列表失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingFeature.value = null
  form.key = ''
  form.name = ''
  form.description = ''
  form.is_pro = false
  modalVisible.value = true
}

function openEdit(record) {
  editingFeature.value = record
  form.key = record.key
  form.name = record.name
  form.description = record.description || ''
  form.is_pro = record.is_pro || false
  modalVisible.value = true
}

async function doSave() {
  try {
    const payload = { key: form.key, name: form.name, description: form.description, is_pro: form.is_pro }
    if (editingFeature.value) {
      await featuresApi.update(editingFeature.value.id, payload)
      message.success('功能更新成功')
    } else {
      await featuresApi.create(payload)
      message.success('功能创建成功')
    }
    modalVisible.value = false
    fetchFeatures()
  } catch (err) {
    message.error(err.response?.data?.detail || '操作失败')
  }
}

function handleSave() {
  if (!editingFeature.value) {
    doSave()
    return
  }
  const old = editingFeature.value
  const warnings = []
  if (old.key !== form.key) {
    warnings.push('修改功能代码将同步迁移所有用户的相关权益记录')
  }
  if (old.is_pro && !form.is_pro) {
    warnings.push('从 Pro 改为免费将清除该功能的所有用户权益记录（该功能变为免费后无需权益即可访问）')
  }
  if (warnings.length > 0) {
    Modal.confirm({
      title: '操作影响提示',
      icon: createVNode(ExclamationCircleOutlined),
      content: warnings.join('；'),
      okText: '确认修改',
      cancelText: '取消',
      onOk: doSave
    })
  } else {
    doSave()
  }
}

function handleDelete(record) {
  Modal.confirm({
    title: '确认删除',
    icon: createVNode(ExclamationCircleOutlined),
    content: `删除功能「${record.name}」将同时清除所有用户的该功能权益，确定要继续吗？`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        await featuresApi.delete(record.id)
        message.success('功能删除成功，相关用户权益已同步清除')
        fetchFeatures()
      } catch (err) {
        message.error(err.response?.data?.detail || '删除失败')
      }
    }
  })
}

onMounted(() => {
  fetchFeatures()
})
</script>

<template>
  <div>
    <a-page-header title="功能管理" sub-title="管理平台功能模块（变更会实时影响用户权益）">
      <template #extra>
        <a-button v-if="auth.hasPermission('feature:create')" type="primary" @click="openCreate">
          <template #icon><PlusOutlined /></template>
          新建功能
        </a-button>
      </template>
    </a-page-header>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="features"
        :loading="loading"
        :row-key="(r) => r.id"
        :pagination="{ pageSize: 15, showTotal: (t) => `共 ${t} 条` }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag v-if="record.is_pro" color="gold">
              <CrownOutlined /> Pro
            </a-tag>
            <a-tag v-else color="default">免费</a-tag>
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button v-if="auth.hasPermission('feature:update')" size="small" @click="openEdit(record)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-button v-if="auth.hasPermission('feature:delete')" size="small" danger @click="handleDelete(record)">
                <template #icon><DeleteOutlined /></template>
                删除
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="modalVisible"
      :title="editingFeature ? '编辑功能' : '新建功能'"
      @ok="handleSave"
      :destroyOnClose="true"
    >
      <a-form layout="vertical">
        <a-form-item label="功能代码 (key)" required>
          <a-input v-model:value="form.key" placeholder="如: chart_advanced" />
        </a-form-item>
        <a-form-item label="功能名称" required>
          <a-input v-model:value="form.name" placeholder="如: 高级图表" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" placeholder="请输入功能描述" :rows="2" />
        </a-form-item>
        <a-form-item label="Pro 专属">
          <a-switch v-model:checked="form.is_pro" checked-children="是" un-checked-children="否" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>
