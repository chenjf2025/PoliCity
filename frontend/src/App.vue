<template>
  <div id="app">
    <!-- 导航栏 - 非登录页显示 -->
    <div class="navbar" v-if="!isLoginPage">
      <span class="navbar-title">城策</span>
      <span class="navbar-subtitle">城市治理决策支持平台</span>
      <div class="navbar-right">
        <el-dropdown @command="handleUserCommand">
          <span class="user-info">
            <el-icon><User /></el-icon>
            <span>{{ currentUser.username }}</span>
            <el-tag v-if="currentUser.role === 'admin'" type="danger" size="small">管理员</el-tag>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon> 个人中心
              </el-dropdown-item>
              <el-dropdown-item v-if="currentUser.role === 'admin'" command="admin">
                <el-icon><Setting /></el-icon> 系统管理
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="main-container" v-if="!isLoginPage">
      <!-- 侧边栏 -->
      <div class="sidebar">
        <el-menu
          :default-active="$route.path"
          class="sidebar-menu"
          router
        >
          <el-menu-item index="/dashboard">
            <el-icon><DataBoard /></el-icon>
            <span>驾驶舱</span>
          </el-menu-item>
          <el-menu-item index="/indicators">
            <el-icon><List /></el-icon>
            <span>指标管理</span>
          </el-menu-item>
          <el-menu-item index="/evaluation">
            <el-icon><DataAnalysis /></el-icon>
            <span>评价详情</span>
          </el-menu-item>
          <el-menu-item index="/simulation">
            <el-icon><Operation /></el-icon>
            <span>政策仿真</span>
          </el-menu-item>
          <el-menu-item index="/benchmark">
            <el-icon><Connection /></el-icon>
            <span>对标分析</span>
          </el-menu-item>
          <el-menu-item index="/chat">
            <el-icon><ChatDotRound /></el-icon>
            <span>AI助手</span>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- 内容区 -->
      <div class="content">
        <router-view />
      </div>
    </div>

    <!-- 登录页单独显示 -->
    <div v-else class="login-page-container">
      <router-view />
    </div>

    <!-- AI对话悬浮球 - 非登录页显示 -->
    <ChatWidget v-if="!isLoginPage" />
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ChatWidget from './components/ChatWidget.vue'

const router = useRouter()
const route = useRoute()

const isLoginPage = computed(() => route.path === '/login')

const currentUser = reactive({
  username: '',
  role: ''
})

const loadUserInfo = () => {
  const userStr = localStorage.getItem('cgdss_user')
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      currentUser.username = user.username || ''
      currentUser.role = user.role || ''
    } catch (e) {
      console.error(e)
    }
  }
}

const handleUserCommand = (command: string) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'admin') {
    router.push('/admin')
  } else if (command === 'logout') {
    localStorage.removeItem('cgdss_token')
    localStorage.removeItem('cgdss_user')
    router.push('/login')
  }
}

onMounted(() => {
  loadUserInfo()
})

// 监听路由变化，重新加载用户信息
watch(() => route.path, () => {
  loadUserInfo()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}
</style>

<style scoped>
.navbar {
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  padding: 0 24px;
  color: white;
}

.navbar-title {
  font-size: 22px;
  font-weight: bold;
  margin-right: 12px;
}

.navbar-subtitle {
  font-size: 14px;
  opacity: 0.9;
}

.navbar-right {
  margin-left: auto;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  transition: all 0.3s;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.2);
}

.main-container {
  display: flex;
  height: calc(100vh - 60px);
}

.sidebar {
  width: 200px;
  background: white;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
}

.sidebar-menu {
  border-right: none;
}

.content {
  flex: 1;
  background: #f5f7fa;
  overflow-y: auto;
  padding: 0;
}

.content > div {
  padding: 0;
}

.login-page-container {
  height: 100vh;
}
</style>
