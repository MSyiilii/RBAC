<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { coursesApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'
import { formatTime } from '../utils/format'
import { PlusOutlined, EditOutlined, DeleteOutlined, TeamOutlined, UserAddOutlined, CheckCircleOutlined } from '@ant-design/icons-vue'

const auth = useAuthStore()
const courses = ref([])
const mySubCourseIds = ref(new Set())
const loading = ref(false)
const modalVisible = ref(false)
const subscriberModalVisible = ref(false)
const editingCourse = ref(null)
const selectedCourse = ref(null)
const subscribers = ref([])

const isCreatorOrAdmin = computed(() => auth.isCreator || auth.isAdmin)

const form = reactive({
  title: '',
  description: '',
  course_type: 'online',
  starts_at: null,
  ends_at: null,
  is_permanent: true
})

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '课程名称', dataIndex: 'title' },
  { title: '类型', key: 'course_type', width: 100 },
  { title: '开始时间', dataIndex: 'starts_at', width: 180, customRender: ({ text }) => formatTime(text) },
  { title: '结束时间', key: 'ends_at', width: 180 },
  { title: '描述', dataIndex: 'description', ellipsis: true },
  { title: '操作', key: 'action', width: 340 }
]

async function fetchCourses() {
  loading.value = true
  try {
    const { data } = await coursesApi.list()
    courses.value = Array.isArray(data) ? data : []
  } catch {
    message.error('获取课程列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchMySubscriptions() {
  try {
    const { data } = await coursesApi.mySubscriptions()
    const ids = new Set()
    for (const s of (Array.isArray(data) ? data : [])) {
      ids.add(s.course_id)
    }
    mySubCourseIds.value = ids
  } catch { /* ignore */ }
}

function isOwnCourse(record) {
  return record.creator_id === auth.user?.id
}

function isSubscribed(record) {
  return mySubCourseIds.value.has(record.id)
}

function openCreate() {
  editingCourse.value = null
  form.title = ''
  form.description = ''
  form.course_type = 'online'
  form.starts_at = null
  form.ends_at = null
  form.is_permanent = true
  modalVisible.value = true
}

function openEdit(record) {
  editingCourse.value = record
  form.title = record.title
  form.description = record.description || ''
  form.course_type = record.course_type || 'online'
  form.starts_at = record.starts_at || null
  form.ends_at = record.ends_at || null
  form.is_permanent = !record.ends_at
  modalVisible.value = true
}

async function handleSave() {
  if (!form.starts_at) {
    message.warning('请选择开始时间')
    return
  }
  try {
    const payload = {
      title: form.title,
      description: form.description,
      course_type: form.course_type,
      starts_at: form.starts_at,
      ends_at: form.is_permanent ? null : form.ends_at
    }
    if (editingCourse.value) {
      await coursesApi.update(editingCourse.value.id, payload)
      message.success('课程更新成功')
    } else {
      await coursesApi.create(payload)
      message.success('课程创建成功')
    }
    modalVisible.value = false
    fetchCourses()
  } catch (err) {
    message.error(err.response?.data?.detail || '操作失败')
  }
}

async function handleDelete(record) {
  try {
    await coursesApi.delete(record.id)
    message.success('课程删除成功')
    fetchCourses()
  } catch (err) {
    message.error(err.response?.data?.detail || '删除失败')
  }
}

async function viewSubscribers(record) {
  selectedCourse.value = record
  try {
    const { data } = await coursesApi.subscribers(record.id)
    subscribers.value = Array.isArray(data) ? data : []
  } catch (err) {
    subscribers.value = []
    if (err.response?.status === 403) {
      message.warning('只有课程创建者可以查看学员列表')
    }
  }
  subscriberModalVisible.value = true
}

async function handleSubscribe(record) {
  try {
    await coursesApi.subscribe(record.id)
    message.success('报名成功！已自动授予 Pro 权益')
    fetchCourses()
    fetchMySubscriptions()
  } catch (err) {
    const status = err.response?.status
    const detail = err.response?.data?.detail
    if (status === 409) {
      message.warning(detail || '已报名该课程，不可重复报名')
    } else if (status === 403) {
      message.warning(detail || '不能报名自己创建的课程')
    } else {
      message.error(detail || '报名失败')
    }
  }
}

onMounted(() => {
  fetchCourses()
  fetchMySubscriptions()
})
</script>

<template>
  <div>
    <a-page-header title="课程管理" sub-title="管理课程及学员报名">
      <template #extra>
        <a-button v-if="isCreatorOrAdmin" type="primary" @click="openCreate">
          <template #icon><PlusOutlined /></template>
          新建课程
        </a-button>
      </template>
    </a-page-header>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="courses"
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

          <template v-if="column.key === 'ends_at'">
            <a-tag v-if="!record.ends_at" color="green">永久有效</a-tag>
            <span v-else>{{ formatTime(record.ends_at) }}</span>
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button v-if="isCreatorOrAdmin" size="small" @click="openEdit(record)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-button size="small" type="primary" ghost @click="viewSubscribers(record)">
                <template #icon><TeamOutlined /></template>
                学员
              </a-button>

              <a-button v-if="isSubscribed(record)" size="small" disabled>
                <template #icon><CheckCircleOutlined /></template>
                已报名
              </a-button>
              <a-tooltip v-else-if="isOwnCourse(record)" title="不能报名自己创建的课程">
                <a-button size="small" disabled>
                  <template #icon><UserAddOutlined /></template>
                  报名
                </a-button>
              </a-tooltip>
              <a-popconfirm
                v-else
                :title="`确定报名「${record.title}」？${record.course_type === 'offline' ? '将获得终身 Pro 权限' : '将获得一年 Pro 权限'}`"
                @confirm="handleSubscribe(record)"
              >
                <a-button size="small">
                  <template #icon><UserAddOutlined /></template>
                  报名
                </a-button>
              </a-popconfirm>

              <a-popconfirm
                v-if="isCreatorOrAdmin"
                title="确定要删除该课程吗？"
                @confirm="handleDelete(record)"
              >
                <a-button size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="modalVisible"
      :title="editingCourse ? '编辑课程' : '新建课程'"
      @ok="handleSave"
      :destroyOnClose="true"
    >
      <a-form layout="vertical">
        <a-form-item label="课程名称" required>
          <a-input v-model:value="form.title" placeholder="请输入课程名称" />
        </a-form-item>
        <a-form-item label="课程类型" required>
          <a-radio-group v-model:value="form.course_type">
            <a-radio value="online">线上课（报名获一年 Pro）</a-radio>
            <a-radio value="offline">线下课（报名获终身 Pro）</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" placeholder="请输入课程描述" :rows="3" />
        </a-form-item>
        <a-form-item label="开始时间" required>
          <a-date-picker
            v-model:value="form.starts_at"
            show-time
            placeholder="请选择开始时间"
            style="width: 100%"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </a-form-item>
        <a-form-item label="永久有效">
          <a-switch v-model:checked="form.is_permanent" checked-children="永久" un-checked-children="有期限" />
        </a-form-item>
        <a-form-item v-if="!form.is_permanent" label="结束时间">
          <a-date-picker
            v-model:value="form.ends_at"
            show-time
            placeholder="请选择结束时间"
            style="width: 100%"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="subscriberModalVisible"
      :title="`${selectedCourse?.title} - 学员列表`"
      :footer="null"
      width="600px"
    >
      <a-empty v-if="subscribers.length === 0" description="暂无学员" />
      <a-table
        v-else
        :data-source="subscribers"
        :row-key="(r) => r.id"
        size="small"
        :pagination="false"
        :columns="[
          { title: '用户ID', dataIndex: 'user_id', width: 80 },
          { title: '报名时间', dataIndex: 'created_at', customRender: ({ text }) => formatTime(text) },
          { title: '状态', dataIndex: 'status' }
        ]"
      />
    </a-modal>
  </div>
</template>
