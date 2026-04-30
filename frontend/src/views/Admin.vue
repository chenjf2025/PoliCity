<template>
  <div class="admin-page">
    <div class="dashboard-card">
      <div class="card-title">系统管理</div>

      <el-tabs v-model="activeTab" class="admin-tabs" @tab-change="onTabChange">
        <!-- 用户管理 -->
        <el-tab-pane label="用户管理" name="users">
          <div class="toolbar">
            <el-button type="primary" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon> 新建用户
            </el-button>
            <el-select v-model="filterStatus" placeholder="状态筛选" style="width: 150px; margin-left: 10px;" @change="loadUsers">
              <el-option label="全部" :value="-2" />
              <el-option label="待审批" :value="0" />
              <el-option label="正常" :value="1" />
              <el-option label="禁用" :value="-1" />
            </el-select>
            <el-button type="success" style="margin-left: 10px;" @click="loadUsers">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>

          <el-table :data="users" stripe style="margin-top: 16px;" v-loading="loadingUsers">
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="phone" label="手机号" width="130" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column prop="full_name" label="姓名" width="100" />
            <el-table-column prop="role" label="角色" width="80">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
                  {{ row.role === 'admin' ? '管理员' : '用户' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_active === 0" type="warning" size="small">待审批</el-tag>
                <el-tag v-else-if="row.is_active === 1" type="success" size="small">正常</el-tag>
                <el-tag v-else type="danger" size="small">禁用</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="注册时间" width="160">
              <template #default="{ row }">
                {{ row.created_at ? new Date(row.created_at).toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button v-if="row.is_active === 0" type="success" size="small" link @click="handleApprove(row)">通过</el-button>
                <el-button v-if="row.is_active === 0" type="danger" size="small" link @click="handleReject(row)">拒绝</el-button>
                <el-button v-if="row.is_active === 1" type="warning" size="small" link @click="handleDisable(row)">禁用</el-button>
                <el-button v-if="row.is_active === -1" type="success" size="small" link @click="handleEnable(row)">启用</el-button>
                <el-button type="primary" size="small" link @click="handleEdit(row)">编辑</el-button>
                <el-button type="danger" size="small" link @click="handleDelete(row)" :disabled="row.username === 'admin'">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 操作日志 -->
        <el-tab-pane label="操作日志" name="logs">
          <div class="toolbar">
            <el-button type="primary" @click="loadLogs">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>

          <el-table :data="logs" stripe style="margin-top: 16px;" v-loading="loadingLogs">
            <el-table-column prop="username" label="操作人" width="120" />
            <el-table-column prop="action" label="操作类型" width="120" />
            <el-table-column prop="detail" label="操作详情" min-width="200" />
            <el-table-column prop="ip_address" label="IP地址" width="130" />
            <el-table-column prop="created_at" label="操作时间" width="160">
              <template #default="{ row }">
                {{ row.created_at ? new Date(row.created_at).toLocaleString() : '-' }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 异常数据审核 -->
        <el-tab-pane label="异常数据" name="anomalies">
          <div class="toolbar">
            <el-select v-model="anomalyStatus" placeholder="状态筛选" style="width: 150px;" @change="loadAnomalies">
              <el-option label="全部" value="" />
              <el-option label="待处理" value="PENDING" />
              <el-option label="已确认" value="CONFIRMED" />
              <el-option label="已忽略" value="IGNORED" />
            </el-select>
            <el-button type="primary" style="margin-left: 10px;" @click="loadAnomalies">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
            <el-button type="success" @click="batchConfirmAnomalies" :disabled="selectedAnomalies.length === 0">
              批量确认
            </el-button>
            <el-button type="warning" @click="batchIgnoreAnomalies" :disabled="selectedAnomalies.length === 0">
              批量忽略
            </el-button>
          </div>

          <el-table :data="anomalies" stripe style="margin-top: 16px;" v-loading="loadingAnomalies" @selection-change="onAnomalySelectionChange">
            <el-table-column type="selection" width="55" />
            <el-table-column prop="indicator_code" label="指标编码" width="120" />
            <el-table-column prop="region_name" label="区域" width="120" />
            <el-table-column prop="report_year" label="年份" width="80" />
            <el-table-column prop="value" label="数值" width="100">
              <template #default="{ row }">
                <span style="color: #f56c6c; font-weight: bold;">{{ row.value }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="anomaly_type" label="异常类型" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.anomaly_type === 'OVER_MAX'" type="danger">超出最大值</el-tag>
                <el-tag v-else-if="row.anomaly_type === 'UNDER_MIN'" type="warning">低于最小值</el-tag>
                <el-tag v-else-if="row.anomaly_type === 'FLUCTUATION'" type="warning">波动过大</el-tag>
                <el-tag v-else-if="row.anomaly_type === 'TREND_CHANGE'" type="info">趋势突变</el-tag>
                <el-tag v-else type="info">{{ row.anomaly_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="异常描述" min-width="200" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'PENDING'" type="warning">待处理</el-tag>
                <el-tag v-else-if="row.status === 'CONFIRMED'" type="danger">已确认</el-tag>
                <el-tag v-else type="info">已忽略</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button v-if="row.status === 'PENDING'" type="success" size="small" link @click="confirmAnomaly(row)">确认</el-button>
                <el-button v-if="row.status === 'PENDING'" type="warning" size="small" link @click="ignoreAnomaly(row)">忽略</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 删除审核 -->
        <el-tab-pane label="删除审核" name="deletes">
          <div class="toolbar">
            <el-button type="primary" @click="loadPendingDeletes">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>

          <el-table :data="pendingDeletes" stripe style="margin-top: 16px;" v-loading="loadingDeletes">
            <el-table-column prop="region_name" label="区域" width="120" />
            <el-table-column prop="indicator_code" label="指标编码" width="120" />
            <el-table-column prop="report_year" label="年份" width="80" />
            <el-table-column prop="raw_value" label="数值" width="100" />
            <el-table-column prop="source_name" label="来源" min-width="150">
              <template #default="{ row }">
                <span v-if="row.source_name">{{ row.source_name }}</span>
                <span v-else style="color: #909399;">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="申请时间" width="160">
              <template #default="{ row }">
                {{ row.updated_at ? new Date(row.updated_at).toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="success" size="small" link @click="approveDelete(row)">批准删除</el-button>
                <el-button type="warning" size="small" link @click="rejectDelete(row)">拒绝</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 创建用户对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建用户" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="3-20位" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="createForm.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="createForm.password" type="password" placeholder="至少8位" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="createForm.role">
            <el-radio label="user">普通用户</el-radio>
            <el-radio label="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑用户" width="500px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editForm.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="editForm.full_name" placeholder="姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="editForm.role" :disabled="editForm.username === 'admin'">
            <el-radio label="user">普通用户</el-radio>
            <el-radio label="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="updating">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { authAPI, dataAPI } from '../api'

const activeTab = ref('users')
const loadingUsers = ref(false)
const loadingLogs = ref(false)
const creating = ref(false)
const updating = ref(false)

// 用户列表
const users = ref<any[]>([])
const filterStatus = ref(-2)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)

// 日志列表
const logs = ref<any[]>([])

// 异常数据列表
const anomalies = ref<any[]>([])
const anomalyStatus = ref('')
const selectedAnomalies = ref<any[]>([])
const loadingAnomalies = ref(false)

// 删除审核列表
const pendingDeletes = ref<any[]>([])
const loadingDeletes = ref(false)

// 创建表单
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  username: '',
  phone: '',
  email: '',
  password: '',
  role: 'user'
})
const createRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '3-20位', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '格式不正确', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '至少8位', trigger: 'blur' }
  ]
}

// 编辑表单
const editFormRef = ref<FormInstance>()
const editForm = reactive({
  id: '',
  username: '',
  phone: '',
  email: '',
  full_name: '',
  role: 'user'
})
const editRules: FormRules = {
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ]
}

const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const status = filterStatus.value === -2 ? undefined : filterStatus.value
    const res: any = await authAPI.getUsers(status)
    users.value = res.users
  } catch (e) {
    console.error(e)
  } finally {
    loadingUsers.value = false
  }
}

const loadLogs = async () => {
  loadingLogs.value = true
  try {
    const res: any = await authAPI.getLogs(100)
    logs.value = res.logs
  } catch (e) {
    console.error(e)
  } finally {
    loadingLogs.value = false
  }
}

// 异常数据相关
const loadAnomalies = async () => {
  loadingAnomalies.value = true
  try {
    const params: any = {}
    if (anomalyStatus.value) params.status = anomalyStatus.value
    const res: any = await dataAPI.listAnomalies(params)
    anomalies.value = res
  } catch (e) {
    console.error(e)
  } finally {
    loadingAnomalies.value = false
  }
}

const onAnomalySelectionChange = (selection: any[]) => {
  selectedAnomalies.value = selection
}

const confirmAnomaly = async (row: any) => {
  try {
    await dataAPI.confirmAnomaly(row.id)
    ElMessage.success('已确认')
    loadAnomalies()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const ignoreAnomaly = async (row: any) => {
  try {
    await dataAPI.ignoreAnomaly(row.id)
    ElMessage.success('已忽略')
    loadAnomalies()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const batchConfirmAnomalies = async () => {
  try {
    const ids = selectedAnomalies.value.map((a: any) => a.id)
    await dataAPI.batchConfirmAnomalies(ids)
    ElMessage.success('批量确认成功')
    loadAnomalies()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const batchIgnoreAnomalies = async () => {
  try {
    const ids = selectedAnomalies.value.map((a: any) => a.id)
    await dataAPI.batchIgnoreAnomalies(ids)
    ElMessage.success('批量忽略成功')
    loadAnomalies()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

// 删除审核相关
const loadPendingDeletes = async () => {
  loadingDeletes.value = true
  try {
    const res: any = await dataAPI.listPendingDeletes()
    pendingDeletes.value = res
  } catch (e) {
    console.error(e)
  } finally {
    loadingDeletes.value = false
  }
}

const approveDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要批准删除吗？数据将被永久删除！', '确认', { type: 'warning' })
    await dataAPI.approveDelete(row.id)
    ElMessage.success('删除已批准')
    loadPendingDeletes()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

const rejectDelete = async (row: any) => {
  try {
    await dataAPI.rejectDelete(row.id)
    ElMessage.success('已拒绝，数据已恢复')
    loadPendingDeletes()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const onTabChange = (tabName: string) => {
  if (tabName === 'anomalies') {
    loadAnomalies()
  } else if (tabName === 'deletes') {
    loadPendingDeletes()
  }
}

const handleCreate = async () => {
  if (!createFormRef.value) return
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    creating.value = true
    try {
      await authAPI.createUser(createForm)
      ElMessage.success('用户创建成功')
      showCreateDialog.value = false
      loadUsers()
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '创建失败')
    } finally {
      creating.value = false
    }
  })
}

const handleEdit = (row: any) => {
  editForm.id = row.id
  editForm.username = row.username
  editForm.phone = row.phone || ''
  editForm.email = row.email || ''
  editForm.full_name = row.full_name || ''
  editForm.role = row.role
  showEditDialog.value = true
}

const handleUpdate = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    updating.value = true
    try {
      await authAPI.updateUser(editForm.id, {
        phone: editForm.phone,
        email: editForm.email,
        full_name: editForm.full_name,
        role: editForm.role
      })
      ElMessage.success('用户更新成功')
      showEditDialog.value = false
      loadUsers()
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '更新失败')
    } finally {
      updating.value = false
    }
  })
}

const handleApprove = async (row: any) => {
  try {
    await authAPI.approveUser(row.id)
    ElMessage.success('已审批通过')
    loadUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const handleReject = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要拒绝该用户的注册申请吗？', '确认', { type: 'warning' })
    await authAPI.rejectUser(row.id)
    ElMessage.success('已拒绝')
    loadUsers()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

const handleDisable = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要禁用该用户吗？', '确认', { type: 'warning' })
    await authAPI.updateUser(row.id, { is_active: -1 })
    ElMessage.success('已禁用')
    loadUsers()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

const handleEnable = async (row: any) => {
  try {
    await authAPI.updateUser(row.id, { is_active: 1 })
    ElMessage.success('已启用')
    loadUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该用户吗？此操作不可恢复！', '危险操作', { type: 'error' })
    await authAPI.deleteUser(row.id)
    ElMessage.success('已删除')
    loadUsers()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadUsers()
  loadLogs()
})
</script>

<style scoped>
.admin-page {
  padding: 20px;
}

.admin-tabs {
  margin-top: 10px;
}

.toolbar {
  display: flex;
  align-items: center;
}
</style>
