<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { permissionsApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'
import { formatTime } from '../utils/format'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'

const auth = useAuthStore()

const permissions = ref([])
const loading = ref(false)
const modalVisible = ref(false)
const editingPerm = ref(null)

const form = reactive({
  key: '',
  name: '',
  description: ''
})

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '权限标识', dataIndex: 'key' },
  { title: '权限名称', dataIndex: 'name' },
  { title: '描述', dataIndex: 'description' },
  { title: '创建时间', dataIndex: 'created_at', width: 180, customRender: ({ text }) => formatTime(text) },
  { title: '操作', key: 'action', width: 200 }
]

async function fetchPermissions() {
  loading.value = true
  try {
    const { data } = await permissionsApi.list()
    permissions.value = Array.isArray(data) ? data : []
  } catch {
    message.error('获取权限列表失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingPerm.value = null
  form.key = ''
  form.name = ''
  form.description = ''
  modalVisible.value = true
}

function openEdit(record) {
  editingPerm.value = record
  form.key = record.key
  form.name = record.name
  form.description = record.description || ''
  modalVisible.value = true
}

async function handleSave() {
  try {
    const payload = { key: form.key, name: form.name, description: form.description }
    if (editingPerm.value) {
      await permissionsApi.update(editingPerm.value.id, payload)
      message.success('权限更新成功')
    } else {
      await permissionsApi.create(payload)
      message.success('权限创建成功')
    }
    modalVisible.value = false
    fetchPermissions()
  } catch (err) {
    message.error(err.response?.data?.detail || '操作失败')
  }
}

async function handleDelete(record) {
  try {
    await permissionsApi.delete(record.id)
    message.success('权限删除成功')
    fetchPermissions()
  } catch (err) {
    message.error(err.response?.data?.detail || '删除失败')
  }
}

onMounted(() => {
  fetchPermissions()
})
</script>

<template>
  <div>
    <a-page-header title="权限管理" sub-title="管理系统权限标识">
      <template #extra>
        <a-button v-if="auth.hasPermission('permission:create')" type="primary" @click="openCreate">
          <template #icon><PlusOutlined /></template>
          新建权限
        </a-button>
      </template>
    </a-page-header>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="permissions"
        :loading="loading"
        :row-key="(r) => r.id"
        :pagination="{ pageSize: 15, showTotal: (t) => `共 ${t} 条` }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button v-if="auth.hasPermission('permission:update')" size="small" @click="openEdit(record)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-popconfirm
                v-if="auth.hasPermission('permission:delete')"
                title="确定要删除该权限吗？"
                @confirm="handleDelete(record)"
              >
                <a-button size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="modalVisible"
      :title="editingPerm ? '编辑权限' : '新建权限'"
      @ok="handleSave"
      :destroyOnClose="true"
    >
      <a-form layout="vertical">
        <a-form-item label="权限标识 (key)" required>
          <a-input v-model:value="form.key" placeholder="如: user:read, course:create" />
        </a-form-item>
        <a-form-item label="权限名称" required>
          <a-input v-model:value="form.name" placeholder="如: 查看用户" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" placeholder="请输入权限描述" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>
