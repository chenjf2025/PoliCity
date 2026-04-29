<template>
  <div id="app">
    <!-- 导航栏 -->
    <div class="navbar">
      <span class="navbar-title">城策</span>
      <span class="navbar-subtitle">城市治理决策支持平台</span>
    </div>

    <div class="main-container">
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

    <!-- AI对话悬浮球 -->
    <ChatWidget />
  </div>
</template>

<script setup lang="ts">
import ChatWidget from './components/ChatWidget.vue'
</script>
