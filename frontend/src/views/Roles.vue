<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { rolesApi, permissionsApi } from '../api/modules'
import { formatTime } from '../utils/format'
import { PlusOutlined, EditOutlined, DeleteOutlined, SettingOutlined } from '@ant-design/icons-vue'

const roles = ref([])
const allPermissions = ref([])
const loading = ref(false)
const modalVisible = ref(false)
const permModalVisible = ref(false)
const editingRole = ref(null)
const selectedRole = ref(null)

const form = reactive({
  name: '',
  description: ''
})

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '角色名称', dataIndex: 'name' },
  { title: '描述', dataIndex: 'description' },
  { title: '权限', dataIndex: 'permissions', key: 'permissions' },
  { title: '创建时间', dataIndex: 'created_at', width: 180, customRender: ({ text }) => formatTime(text) },
  { title: '操作', key: 'action', width: 280 }
]

async function fetchRoles() {
  loading.value = true
  try {
    const { data } = await rolesApi.list()
    roles.value = Array.isArray(data) ? data : data.items || []
  } catch {
    message.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchPermissions() {
  try {
    const { data } = await permissionsApi.list()
    allPermissions.value = Array.isArray(data) ? data : data.items || []
  } catch {
    // ignore
  }
}

function openCreate() {
  editingRole.value = null
  form.name = ''
  form.description = ''
  modalVisible.value = true
}

function openEdit(record) {
  editingRole.value = record
  form.name = record.name
  form.description = record.description || ''
  modalVisible.value = true
}

async function handleSave() {
  try {
    if (editingRole.value) {
      await rolesApi.update(editingRole.value.id, {
        name: form.name,
        description: form.description
      })
      message.success('角色更新成功')
    } else {
      await rolesApi.create({
        name: form.name,
        description: form.description
      })
      message.success('角色创建成功')
    }
    modalVisible.value = false
    fetchRoles()
  } catch (err) {
    message.error(err.response?.data?.detail || '操作失败')
  }
}

async function handleDelete(record) {
  try {
    await rolesApi.delete(record.id)
    message.success('角色删除成功')
    fetchRoles()
  } catch (err) {
    message.error(err.response?.data?.detail || '删除失败')
  }
}

function openPermModal(record) {
  selectedRole.value = record
  permModalVisible.value = true
}

async function assignPermission(permId) {
  try {
    await rolesApi.assignPermission(selectedRole.value.id, permId)
    message.success('权限分配成功')
    fetchRoles()
  } catch (err) {
    message.error(err.response?.data?.detail || '分配权限失败')
  }
}

async function revokePermission(roleId, permId) {
  try {
    await rolesApi.revokePermission(roleId, permId)
    message.success('权限移除成功')
    fetchRoles()
  } catch (err) {
    message.error(err.response?.data?.detail || '移除权限失败')
  }
}

onMounted(() => {
  fetchRoles()
  fetchPermissions()
})
</script>

<template>
  <div>
    <a-page-header title="角色管理" sub-title="管理系统角色及权限分配">
      <template #extra>
        <a-button type="primary" @click="openCreate">
          <template #icon><PlusOutlined /></template>
          新建角色
        </a-button>
      </template>
    </a-page-header>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="roles"
        :loading="loading"
        :row-key="(r) => r.id"
        :pagination="{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'permissions'">
            <a-tag
              v-for="perm in (record.permissions || [])"
              :key="perm.id"
              color="green"
              closable
              @close="revokePermission(record.id, perm.id)"
            >
              {{ perm.name }}
            </a-tag>
            <a-tag
              style="border-style: dashed; cursor: pointer"
              @click="openPermModal(record)"
            >
              <PlusOutlined /> 添加权限
            </a-tag>
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="openEdit(record)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-button size="small" @click="openPermModal(record)">
                <template #icon><SettingOutlined /></template>
                权限
              </a-button>
              <a-popconfirm
                title="确定要删除该角色吗？"
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

    <!-- 创建/编辑角色 Modal -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingRole ? '编辑角色' : '新建角色'"
      @ok="handleSave"
      :destroyOnClose="true"
    >
      <a-form layout="vertical">
        <a-form-item label="角色名称" required>
          <a-input v-model:value="form.name" placeholder="请输入角色名称" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" placeholder="请输入角色描述" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 分配权限 Modal -->
    <a-modal
      v-model:open="permModalVisible"
      title="分配权限"
      :footer="null"
    >
      <a-list :data-source="allPermissions" size="small">
        <template #renderItem="{ item }">
          <a-list-item>
            <template #actions>
              <a-button type="link" size="small" @click="assignPermission(item.id)">
                分配
              </a-button>
            </template>
            <a-list-item-meta :title="item.name" :description="item.key" />
          </a-list-item>
        </template>
      </a-list>
    </a-modal>
  </div>
</template>
