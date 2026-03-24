<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { usersApi, rolesApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'
import { formatTime } from '../utils/format'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'

const auth = useAuthStore()

const users = ref([])
const allRoles = ref([])
const loading = ref(false)
const modalVisible = ref(false)
const roleModalVisible = ref(false)
const editingUser = ref(null)
const selectedUserId = ref(null)

const form = reactive({
  username: '',
  email: '',
  password: '',
  is_active: true
})

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '用户名', dataIndex: 'username' },
  { title: '邮箱', dataIndex: 'email' },
  {
    title: '状态',
    dataIndex: 'is_active',
    customRender: ({ text }) => text ? '启用' : '禁用'
  },
  { title: '角色', dataIndex: 'roles', key: 'roles' },
  { title: '创建时间', dataIndex: 'created_at', width: 180, customRender: ({ text }) => formatTime(text) },
  { title: '操作', key: 'action', width: 280 }
]

async function fetchUsers() {
  loading.value = true
  try {
    const { data } = await usersApi.list()
    users.value = Array.isArray(data) ? data : data.items || []
  } catch {
    message.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchRoles() {
  try {
    const { data } = await rolesApi.list()
    allRoles.value = Array.isArray(data) ? data : data.items || []
  } catch {
    // ignore
  }
}

function openCreate() {
  editingUser.value = null
  form.username = ''
  form.email = ''
  form.password = ''
  form.is_active = true
  modalVisible.value = true
}

function openEdit(record) {
  editingUser.value = record
  form.username = record.username
  form.email = record.email || ''
  form.password = ''
  form.is_active = record.is_active
  modalVisible.value = true
}

async function handleSave() {
  try {
    if (editingUser.value) {
      const payload = { username: form.username, email: form.email, is_active: form.is_active }
      if (form.password) payload.password = form.password
      await usersApi.update(editingUser.value.id, payload)
      message.success('用户更新成功')
    } else {
      await usersApi.create({
        username: form.username,
        email: form.email,
        password: form.password,
        is_active: form.is_active
      })
      message.success('用户创建成功')
    }
    modalVisible.value = false
    fetchUsers()
  } catch (err) {
    message.error(err.response?.data?.detail || '操作失败')
  }
}

async function handleDelete(record) {
  try {
    await usersApi.delete(record.id)
    message.success('用户删除成功')
    fetchUsers()
  } catch (err) {
    message.error(err.response?.data?.detail || '删除失败')
  }
}

function openRoleModal(record) {
  selectedUserId.value = record.id
  roleModalVisible.value = true
}

async function assignRole(roleId) {
  try {
    await usersApi.assignRole(selectedUserId.value, roleId)
    message.success('角色分配成功')
    fetchUsers()
  } catch (err) {
    message.error(err.response?.data?.detail || '分配角色失败')
  }
}

async function revokeRole(userId, roleId) {
  try {
    await usersApi.revokeRole(userId, roleId)
    message.success('角色移除成功')
    fetchUsers()
  } catch (err) {
    message.error(err.response?.data?.detail || '移除角色失败')
  }
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
})
</script>

<template>
  <div>
    <a-page-header title="用户管理" sub-title="管理系统用户及角色分配">
      <template #extra>
        <a-button v-if="auth.hasPermission('user:create')" type="primary" @click="openCreate">
          <template #icon><PlusOutlined /></template>
          新建用户
        </a-button>
      </template>
    </a-page-header>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="users"
        :loading="loading"
        :row-key="(r) => r.id"
        :pagination="{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'roles'">
            <a-tag
              v-for="role in (record.roles || [])"
              :key="role.id"
              color="blue"
              :closable="auth.hasPermission('role:assign')"
              @close="revokeRole(record.id, role.id)"
            >
              {{ role.name }}
            </a-tag>
            <a-tag
              v-if="auth.hasPermission('role:assign')"
              style="border-style: dashed; cursor: pointer"
              @click="openRoleModal(record)"
            >
              <PlusOutlined /> 添加角色
            </a-tag>
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button v-if="auth.hasPermission('user:update')" size="small" @click="openEdit(record)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-popconfirm
                v-if="auth.hasPermission('user:delete')"
                title="确定要删除该用户吗？"
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

    <!-- 创建/编辑用户 Modal -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingUser ? '编辑用户' : '新建用户'"
      @ok="handleSave"
      :destroyOnClose="true"
    >
      <a-form layout="vertical">
        <a-form-item label="用户名" required>
          <a-input v-model:value="form.username" placeholder="请输入用户名" />
        </a-form-item>
        <a-form-item label="邮箱">
          <a-input v-model:value="form.email" placeholder="请输入邮箱" />
        </a-form-item>
        <a-form-item :label="editingUser ? '新密码（留空不修改）' : '密码'" :required="!editingUser">
          <a-input-password v-model:value="form.password" placeholder="请输入密码" />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="form.is_active" checked-children="启用" un-checked-children="禁用" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 分配角色 Modal -->
    <a-modal
      v-model:open="roleModalVisible"
      title="分配角色"
      :footer="null"
    >
      <a-list :data-source="allRoles" size="small">
        <template #renderItem="{ item }">
          <a-list-item>
            <template #actions>
              <a-button type="link" size="small" @click="assignRole(item.id)">
                分配
              </a-button>
            </template>
            <a-list-item-meta :title="item.name" :description="item.description" />
          </a-list-item>
        </template>
      </a-list>
    </a-modal>
  </div>
</template>
