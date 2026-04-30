<template>
  <div class="profile-page">
    <div class="dashboard-card">
      <div class="card-title">个人中心</div>

      <el-row :gutter="20">
        <el-col :span="16">
          <el-card shadow="hover">
            <template #header>
              <span>基本信息</span>
            </template>
            <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-width="100px">
              <el-form-item label="用户名">
                <el-input v-model="profileForm.username" disabled />
              </el-form-item>
              <el-form-item label="手机号" prop="phone">
                <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
              </el-form-item>
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
              </el-form-item>
              <el-form-item label="姓名" prop="full_name">
                <el-input v-model="profileForm.full_name" placeholder="请输入姓名" />
              </el-form-item>
              <el-form-item label="注册时间">
                <el-input :value="profileForm.created_at" disabled />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleUpdateProfile" :loading="saving">
                  保存修改
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <el-card shadow="hover" style="margin-top: 20px;">
            <template #header>
              <span>修改密码</span>
            </template>
            <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px">
              <el-form-item label="原密码" prop="old_password">
                <el-input v-model="passwordForm.old_password" type="password" placeholder="请输入原密码" show-password />
              </el-form-item>
              <el-form-item label="新密码" prop="new_password">
                <el-input v-model="passwordForm.new_password" type="password" placeholder="至少8位，含大小写字母和数字" show-password />
              </el-form-item>
              <el-form-item label="确认密码" prop="confirm_password">
                <el-input v-model="passwordForm.confirm_password" type="password" placeholder="再次输入新密码" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleChangePassword" :loading="changingPwd">
                  修改密码
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>
              <span>账号信息</span>
            </template>
            <div class="user-info">
              <div class="avatar-circle">
                <el-icon :size="48"><User /></el-icon>
              </div>
              <div class="info-item">
                <span class="label">用户名：</span>
                <span class="value">{{ userInfo.username }}</span>
              </div>
              <div class="info-item">
                <span class="label">角色：</span>
                <el-tag :type="userInfo.role === 'admin' ? 'danger' : 'success'" size="small">
                  {{ userInfo.role === 'admin' ? '管理员' : '普通用户' }}
                </el-tag>
              </div>
              <div class="info-item">
                <span class="label">状态：</span>
                <el-tag type="success" size="small">正常</el-tag>
              </div>
            </div>
          </el-card>

          <el-card shadow="hover" style="margin-top: 20px;">
            <template #header>
              <span>快捷操作</span>
            </template>
            <div class="quick-actions">
              <el-button type="primary" plain style="width: 100%; margin-bottom: 10px;" @click="$router.push('/dashboard')">
                返回首页
              </el-button>
              <el-button type="danger" plain style="width: 100%;" @click="handleLogout">
                退出登录
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { authAPI } from '../api'

const router = useRouter()
const saving = ref(false)
const changingPwd = ref(false)
const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

const userInfo = reactive({
  username: '',
  role: ''
})

const profileForm = reactive({
  username: '',
  phone: '',
  email: '',
  full_name: '',
  created_at: ''
})

const profileRules: FormRules = {
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ]
}

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirm = (rule: any, value: any, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

const loadProfile = async () => {
  try {
    const res: any = await authAPI.getProfile()
    profileForm.username = res.username
    profileForm.phone = res.phone || ''
    profileForm.email = res.email || ''
    profileForm.full_name = res.full_name || ''
    profileForm.created_at = res.created_at ? new Date(res.created_at).toLocaleString() : ''
    userInfo.username = res.username
    userInfo.role = res.role
  } catch (e) {
    console.error(e)
  }
}

const handleUpdateProfile = async () => {
  saving.value = true
  try {
    await authAPI.updateProfile({
      phone: profileForm.phone,
      email: profileForm.email,
      full_name: profileForm.full_name
    })
    ElMessage.success('信息更新成功')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
  } finally {
    saving.value = false
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    changingPwd.value = true
    try {
      await authAPI.changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password
      })
      ElMessage.success('密码修改成功')
      passwordForm.old_password = ''
      passwordForm.new_password = ''
      passwordForm.confirm_password = ''
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '修改失败')
    } finally {
      changingPwd.value = false
    }
  })
}

const handleLogout = () => {
  localStorage.removeItem('cgdss_token')
  localStorage.removeItem('cgdss_user')
  router.push('/login')
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  padding: 20px;
}

.user-info {
  text-align: center;
}

.avatar-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.info-item {
  margin-bottom: 12px;
  text-align: left;
}

.info-item .label {
  color: #666;
}

.info-item .value {
  font-weight: 500;
}

.quick-actions {
  display: flex;
  flex-direction: column;
}
</style>
