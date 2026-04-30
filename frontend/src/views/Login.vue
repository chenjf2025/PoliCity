<template>
  <div class="login-page">
    <div class="login-box">
      <div class="login-header">
        <h2>城策平台</h2>
        <p>城市治理决策支持系统</p>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" label-position="top">
            <el-form-item prop="username">
              <el-input v-model="loginForm.username" placeholder="用户名" size="large" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="密码" size="large" prefix-icon="Lock" show-password @keydown.enter="handleLogin" />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="loginForm.remember">7天内免登录</el-checkbox>
              <el-link type="primary" style="margin-left: auto;" @click="activeTab = 'forgot'">忘记密码？</el-link>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="large" style="width: 100%;" :loading="loading" @click="handleLogin">
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" label-position="top">
            <el-form-item prop="username">
              <el-input v-model="registerForm.username" placeholder="用户名（3-20位）" size="large" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="phone">
              <el-input v-model="registerForm.phone" placeholder="手机号" size="large" prefix-icon="Phone" />
            </el-form-item>
            <el-form-item prop="email">
              <el-input v-model="registerForm.email" placeholder="邮箱" size="large" prefix-icon="Message" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="registerForm.password" type="password" placeholder="密码（至少8位，含大小写字母和数字）" size="large" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" size="large" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="large" style="width: 100%;" :loading="loading" @click="handleRegister">
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="忘记密码" name="forgot">
          <el-form ref="forgotFormRef" :model="forgotForm" :rules="forgotRules" label-position="top">
            <el-form-item prop="phone">
              <el-input v-model="forgotForm.phone" placeholder="请输入注册手机号" size="large" prefix-icon="Phone" />
            </el-form-item>
            <el-form-item>
              <el-button :loading="sendingCode" style="width: 100%;" size="large" @click="handleSendCode">
                发送验证码
              </el-button>
            </el-form-item>
            <el-form-item prop="code" v-if="forgotForm.codeSent">
              <el-input v-model="forgotForm.code" placeholder="输入验证码" size="large" prefix-icon="Key" />
            </el-form-item>
            <el-form-item prop="newPassword" v-if="forgotForm.codeSent">
              <el-input v-model="forgotForm.newPassword" type="password" placeholder="新密码（至少8位，含大小写字母和数字）" size="large" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item v-if="forgotForm.codeSent">
              <el-button type="primary" size="large" style="width: 100%;" :loading="loading" @click="handleResetPassword">
                重置密码
              </el-button>
            </el-form-item>
          </el-form>
          <div style="text-align: center; margin-top: 16px;">
            <el-link type="primary" @click="activeTab = 'login'">返回登录</el-link>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 首次登录修改密码对话框 -->
    <el-dialog v-model="changePasswordDialogVisible" title="首次登录请修改密码" width="400px" :close-on-click-modal="false" :show-close="false">
      <el-form ref="changePwdFormRef" :model="changePwdForm" :rules="changePwdRules" label-position="top">
        <el-form-item prop="newPassword">
          <el-input v-model="changePwdForm.newPassword" type="password" placeholder="新密码（至少8位，含大小写字母和数字）" size="large" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="changePwdForm.confirmPassword" type="password" placeholder="确认密码" size="large" prefix-icon="Lock" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" size="large" style="width: 100%;" :loading="loading" @click="handleChangePassword">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { authAPI } from '../api'

const router = useRouter()
const activeTab = ref('login')
const loading = ref(false)
const sendingCode = ref(false)
const changePasswordDialogVisible = ref(false)

// 登录表单
const loginFormRef = ref<FormInstance>()
const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})
const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 注册表单
const registerFormRef = ref<FormInstance>()
const registerForm = reactive({
  username: '',
  phone: '',
  email: '',
  password: '',
  confirmPassword: ''
})
const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名3-20位', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 忘记密码表单
const forgotFormRef = ref<FormInstance>()
const forgotForm = reactive({
  phone: '',
  code: '',
  newPassword: '',
  codeSent: false
})
const forgotRules: FormRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ]
}

// 修改密码表单
const changePwdFormRef = ref<FormInstance>()
const changePwdForm = reactive({
  newPassword: '',
  confirmPassword: ''
})
const validateChangeConfirm = (rule: any, value: any, callback: any) => {
  if (value !== changePwdForm.newPassword) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}
const changePwdRules: FormRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateChangeConfirm, trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res: any = await authAPI.login(loginForm)
      localStorage.setItem('cgdss_token', res.token)
      localStorage.setItem('cgdss_user', JSON.stringify(res.user))

      if (res.must_change_password) {
        changePasswordDialogVisible.value = true
      } else {
        router.push('/dashboard')
      }
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '登录失败')
    } finally {
      loading.value = false
    }
  })
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authAPI.register(registerForm)
      ElMessage.success('注册成功，请等待管理员审批')
      activeTab.value = 'login'
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '注册失败')
    } finally {
      loading.value = false
    }
  })
}

const handleSendCode = async () => {
  if (!forgotForm.phone || !/^1[3-9]\d{9}$/.test(forgotForm.phone)) {
    ElMessage.warning('请输入正确的手机号')
    return
  }
  sendingCode.value = true
  try {
    await authAPI.forgotPassword(forgotForm.phone)
    forgotForm.codeSent = true
    ElMessage.success('验证码已发送')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  } finally {
    sendingCode.value = false
  }
}

const handleResetPassword = async () => {
  if (!forgotForm.code || !forgotForm.newPassword) {
    ElMessage.warning('请填写完整')
    return
  }
  loading.value = true
  try {
    await authAPI.resetPassword(forgotForm.phone, forgotForm.code, forgotForm.newPassword)
    ElMessage.success('密码重置成功')
    activeTab.value = 'login'
    forgotForm.codeSent = false
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '重置失败')
  } finally {
    loading.value = false
  }
}

const handleChangePassword = async () => {
  if (!changePwdFormRef.value) return
  await changePwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authAPI.changePassword({
        old_password: 'admin888',
        new_password: changePwdForm.newPassword
      })
      ElMessage.success('密码修改成功')
      changePasswordDialogVisible.value = false
      router.push('/dashboard')
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '修改失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 420px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 0;
  font-size: 28px;
  color: #333;
}

.login-header p {
  margin: 8px 0 0;
  color: #666;
  font-size: 14px;
}

.login-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.login-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  height: 40px;
  line-height: 40px;
}
</style>
