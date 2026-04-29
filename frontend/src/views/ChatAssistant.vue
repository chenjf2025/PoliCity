<template>
  <div class="chat-page">
    <div class="dashboard-card">
      <div class="card-title">AI智能助手</div>

      <div class="chat-container-full">
        <!-- 左侧会话列表 -->
        <div class="session-panel" v-if="sessionPanelVisible">
          <div class="session-header">
            <span>会话历史</span>
            <el-button text @click="createNewSession">
              <el-icon><Plus /></el-icon> 新会话
            </el-button>
          </div>
          <div class="session-list">
            <div
              v-for="session in sessions"
              :key="session.id"
              :class="['session-item', { active: session.id === currentSessionId }]"
              @click="switchSession(session.id)"
            >
              <div class="session-info">
                <div class="session-name" v-if="editingSessionId !== session.id" @dblclick="startEditSession(session)">
                  {{ session.name }}
                </div>
                <el-input
                  v-else
                  v-model="editingSessionName"
                  size="small"
                  @blur="finishEditSession"
                  @keydown.enter="finishEditSession"
                  ref="sessionNameInput"
                />
                <div class="session-time">{{ formatTime(session.updatedAt) }}</div>
              </div>
              <el-dropdown trigger="click" @command="(cmd: string) => handleSessionCommand(cmd, session)">
                <el-icon><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="rename">重命名</el-dropdown-item>
                    <el-dropdown-item command="export">导出</el-dropdown-item>
                    <el-dropdown-item command="delete" style="color: #f56c6c;">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            <el-empty v-if="sessions.length === 0" description="暂无会话" :image-size="60" />
          </div>
        </div>

        <!-- 切换面板按钮 -->
        <div class="toggle-panel-btn" @click="sessionPanelVisible = !sessionPanelVisible">
          <el-icon v-if="sessionPanelVisible"><ArrowLeft /></el-icon>
          <el-icon v-else><ArrowRight /></el-icon>
        </div>

        <!-- 聊天区域 -->
        <div class="chat-main">
          <div class="messages-list" ref="messagesRef">
            <div v-for="(msg, idx) in currentMessages" :key="msg.id" :class="['message-item', msg.role]">
              <div class="avatar">
                <el-icon v-if="msg.role === 'user'" :size="24"><User /></el-icon>
                <el-icon v-else :size="24"><Robot /></el-icon>
              </div>
              <div class="content">
                <div class="message-text">
                  <div v-if="msg.role === 'user'" class="user-text">{{ msg.content }}</div>
                  <div v-else class="markdown-content" v-html="renderMarkdown(msg.content)"></div>
                </div>
                <!-- 助手消息操作按钮 -->
                <div class="message-actions" v-if="msg.role === 'assistant'">
                  <el-tooltip content="复制">
                    <el-icon @click="copyMessage(msg.content)"><CopyDocument /></el-icon>
                  </el-tooltip>
                  <el-tooltip :content="msg.liked ? '取消收藏' : '收藏'">
                    <el-icon @click="toggleLike(msg)" :style="{ color: msg.liked ? '#f56c6c' : '' }"><Star /></el-icon>
                  </el-tooltip>
                </div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
            </div>
            <div v-if="loading" class="message-item assistant">
              <div class="avatar">
                <el-icon :size="24"><Robot /></el-icon>
              </div>
              <div class="content">
                <div class="message-text">
                  <div class="markdown-content"><el-icon class="is-loading"><Loading /></el-icon> 思考中...</div>
                </div>
              </div>
            </div>
            <!-- 追问建议 -->
            <div v-if="suggestions.length > 0" class="suggestions">
              <div class="suggestions-title">猜你想问：</div>
              <div class="suggestions-list">
                <el-tag
                  v-for="suggestion in suggestions"
                  :key="suggestion"
                  class="suggestion-tag"
                  @click="sendSuggestion(suggestion)"
                >
                  {{ suggestion }}
                </el-tag>
              </div>
            </div>
          </div>

          <div class="chat-input-area">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="输入您的问题，例如：'为什么我们区的文化得分偏低？'"
              @keydown.ctrl.enter="sendMessage"
            />
            <div style="margin-top: 12px; text-align: right;">
              <span style="color: #909399; font-size: 12px; margin-right: 12px;">Ctrl+Enter 发送</span>
              <el-button @click="exportCurrentSession" :disabled="currentMessages.length === 0">导出对话</el-button>
              <el-button @click="clearCurrentSession" :disabled="currentMessages.length === 0">清空</el-button>
              <el-button type="primary" @click="sendMessage" :loading="loading">
                发送
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { difyChatStream } from '../api'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import { ElMessage } from 'element-plus'
import { CopyDocument, Star, Plus, MoreFilled, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  time: string
  liked?: boolean
}

interface Session {
  id: string
  name: string
  messages: Message[]
  createdAt: string
  updatedAt: string
}

const STORAGE_KEY = 'cgdss_chat_sessions'

// 状态
const sessions = ref<Session[]>([])
const currentSessionId = ref<string>('')
const inputMessage = ref('')
const loading = ref(false)
const messagesRef = ref<HTMLElement>()
const currentAssistantMsg = ref<Message | null>(null)
const sessionPanelVisible = ref(true)
const editingSessionId = ref<string>('')
const editingSessionName = ref('')
const suggestions = ref<string[]>([])

// 计算当前会话的消息
const currentMessages = computed(() => {
  const session = sessions.value.find(s => s.id === currentSessionId.value)
  return session?.messages || []
})

// 生成唯一ID
const generateId = () => Math.random().toString(36).substring(2, 15)

// 格式化时间
const formatTime = (timeStr: string) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString()
}

// 加载会话
const loadSessions = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      sessions.value = JSON.parse(stored)
      if (sessions.value.length > 0) {
        currentSessionId.value = sessions.value[0].id
      }
    }
  } catch (e) {
    console.error('Failed to load sessions:', e)
  }
}

// 保存会话
const saveSessions = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.value))
  } catch (e) {
    console.error('Failed to save sessions:', e)
  }
}

// 创建新会话
const createNewSession = () => {
  const newSession: Session = {
    id: generateId(),
    name: '新会话',
    messages: [{
      id: generateId(),
      role: 'assistant',
      content: '您好！我是城策AI助手。我可以帮您：\n1. 分析城市发展状况和评价指标\n2. 解读雷达图和短板指标\n3. 解答政策仿真相关问题\n4. 提供城市治理建议\n\n请问有什么可以帮助您？',
      time: new Date().toLocaleTimeString()
    }],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
  sessions.value.unshift(newSession)
  currentSessionId.value = newSession.id
  saveSessions()
}

// 切换会话
const switchSession = (id: string) => {
  currentSessionId.value = id
}

// 开始编辑会话名
const startEditSession = (session: Session) => {
  editingSessionId.value = session.id
  editingSessionName.value = session.name
  nextTick(() => {
    const input = document.querySelector('.session-item.active .el-input__inner') as HTMLInputElement
    input?.focus()
  })
}

// 完成编辑会话名
const finishEditSession = () => {
  if (!editingSessionId.value) return
  const session = sessions.value.find(s => s.id === editingSessionId.value)
  if (session && editingSessionName.value.trim()) {
    session.name = editingSessionName.value.trim()
    session.updatedAt = new Date().toISOString()
    saveSessions()
  }
  editingSessionId.value = ''
}

// 处理会话操作
const handleSessionCommand = (command: string, session: Session) => {
  if (command === 'rename') {
    startEditSession(session)
  } else if (command === 'export') {
    exportSession(session)
  } else if (command === 'delete') {
    deleteSession(session.id)
  }
}

// 删除会话
const deleteSession = (id: string) => {
  const idx = sessions.value.findIndex(s => s.id === id)
  if (idx !== -1) {
    sessions.value.splice(idx, 1)
    if (currentSessionId.value === id) {
      currentSessionId.value = sessions.value[0]?.id || ''
    }
    saveSessions()
  }
}

// 导出指定会话
const exportSession = (session: Session) => {
  let content = `# ${session.name}\n\n`
  session.messages.forEach(msg => {
    const role = msg.role === 'user' ? '用户' : '助手'
    content += `## ${role} (${msg.time})\n\n${msg.content}\n\n---\n\n`
  })
  downloadMarkdown(content, session.name)
}

// 导出当前会话
const exportCurrentSession = () => {
  const session = sessions.value.find(s => s.id === currentSessionId.value)
  if (session) {
    exportSession(session)
  }
}

// 下载Markdown文件
const downloadMarkdown = (content: string, filename: string) => {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${filename}_${Date.now()}.md`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 清空当前会话
const clearCurrentSession = () => {
  const session = sessions.value.find(s => s.id === currentSessionId.value)
  if (session) {
    session.messages = [{
      id: generateId(),
      role: 'assistant',
      content: '会话已清空。请问有什么可以帮助您？',
      time: new Date().toLocaleTimeString()
    }]
    session.updatedAt = new Date().toISOString()
    saveSessions()
  }
}

// 复制消息
const copyMessage = (content: string) => {
  navigator.clipboard.writeText(content).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 收藏/取消收藏
const toggleLike = (msg: Message) => {
  msg.liked = !msg.liked
  const session = sessions.value.find(s => s.id === currentSessionId.value)
  if (session) {
    session.updatedAt = new Date().toISOString()
    saveSessions()
  }
}

// 发送追问建议
const sendSuggestion = (suggestion: string) => {
  inputMessage.value = suggestion
  sendMessage()
}

// 获取当前会话
const getCurrentSession = (): Session | null => {
  let session = sessions.value.find(s => s.id === currentSessionId.value)
  if (!session) {
    createNewSession()
    session = sessions.value.find(s => s.id === currentSessionId.value)
  }
  return session || null
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const query = inputMessage.value.trim()
  inputMessage.value = ''

  const session = getCurrentSession()
  if (!session) return

  // 添加用户消息
  const userMsg: Message = {
    id: generateId(),
    role: 'user',
    content: query,
    time: new Date().toLocaleTimeString()
  }
  session.messages.push(userMsg)

  // 自动命名会话
  if (session.messages.length === 2) {
    session.name = query.substring(0, 20) + (query.length > 20 ? '...' : '')
  }
  session.updatedAt = new Date().toISOString()
  saveSessions()

  scrollToBottom()

  loading.value = true
  suggestions.value = []

  // 创建空的助手消息用于流式更新
  currentAssistantMsg.value = {
    id: generateId(),
    role: 'assistant',
    content: '',
    time: new Date().toLocaleTimeString()
  }
  session.messages.push(currentAssistantMsg.value)

  try {
    const response = await difyChatStream({
      query,
      user_id: 'web_user'
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    if (!reader) {
      throw new Error('No response body')
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.event === 'message' || data.event === 'assistant' || data.event === 'agent_message') {
              const contentChunk = data.answer || data.content || data.message || ''
              if (contentChunk && currentAssistantMsg.value) {
                currentAssistantMsg.value.content += contentChunk
                scrollToBottom()
              }
            } else if (data.event === 'message_end') {
              loading.value = false
              session.updatedAt = new Date().toISOString()
              saveSessions()
              // 生成追问建议
              generateSuggestions()
            } else if (data.event === 'error' || data.error) {
              console.error('Stream error:', data.error || data.message)
              loading.value = false
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    loading.value = false

    if (!currentAssistantMsg.value?.content) {
      currentAssistantMsg.value.content = '抱歉，我现在无法回答这个问题。'
    }

  } catch (error) {
    console.error('Chat error:', error)
    if (currentAssistantMsg.value) {
      currentAssistantMsg.value.content = '抱歉，发生了错误，请稍后再试。'
    }
    loading.value = false
  }

  scrollToBottom()
}

// 生成追问建议（基于当前回答简单生成）
const generateSuggestions = () => {
  const lastAssistantMsg = currentMessages.value.filter(m => m.role === 'assistant').pop()
  if (!lastAssistantMsg) return

  // 简单的建议生成，实际可由后端提供
  const suggestionList = [
    '请详细说明这个指标的计算方式？',
    '有什么具体的提升建议吗？',
    '跟其他城市相比有什么优势？'
  ]
  suggestions.value = suggestionList
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 配置marked
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true
})

const renderMarkdown = (content: string): string => {
  if (!content) return ''
  return marked.parse(content) as string
}

// 初始化
onMounted(() => {
  loadSessions()
  if (sessions.value.length === 0) {
    createNewSession()
  }
})
</script>

<style scoped>
.chat-container-full {
  display: flex;
  height: calc(100vh - 280px);
  position: relative;
}

.session-panel {
  width: 250px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-right: 12px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.session-header {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}

.session-item:hover {
  background: #e4e7ed;
}

.session-item.active {
  background: #409eff;
  color: white;
}

.session-item.active .session-time {
  color: rgba(255,255,255,0.8);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-name {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.toggle-panel-btn {
  position: absolute;
  left: 258px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 60px;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 0 8px 8px 0;
  z-index: 10;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.messages-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.message-item {
  display: flex;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.message-item.assistant .avatar {
  background: #67c23a;
}

.content {
  max-width: 70%;
  margin: 0 12px;
  position: relative;
}

.user-text {
  white-space: pre-wrap;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.message-item.user .message-text {
  background: #409eff;
  color: white;
  border-bottom-right-radius: 2px;
}

.message-item.assistant .message-text {
  background: white;
  color: #303133;
  border-bottom-left-radius: 2px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-item:hover .message-actions {
  opacity: 1;
}

.message-actions .el-icon {
  cursor: pointer;
  color: #909399;
  font-size: 16px;
}

.message-actions .el-icon:hover {
  color: #409eff;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.message-item.user .message-time {
  text-align: left;
}

.suggestions {
  margin-top: 16px;
  padding: 12px;
  background: white;
  border-radius: 8px;
}

.suggestions-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.suggestions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-tag {
  cursor: pointer;
}

.chat-input-area {
  margin-top: 20px;
  padding: 16px;
  background: white;
  border-radius: 8px;
}

/* Markdown样式 */
.markdown-content {
  font-size: 14px;
  line-height: 1.6;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  margin-top: 12px;
  margin-bottom: 8px;
  font-weight: 600;
}

.markdown-content :deep(h1) { font-size: 1.4em; }
.markdown-content :deep(h2) { font-size: 1.2em; }
.markdown-content :deep(h3) { font-size: 1.1em; }

.markdown-content :deep(p) {
  margin: 8px 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(code) {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}

.markdown-content :deep(pre) {
  background: #f6f8fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #dfe2e5;
  padding: 6px 12px;
  text-align: left;
}

.markdown-content :deep(th) {
  background: #f6f8fa;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #dfe2e5;
  padding-left: 12px;
  margin: 8px 0;
  color: #666;
}

.markdown-content :deep(a) {
  color: #409eff;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid #dfe2e5;
  margin: 16px 0;
}

.markdown-content :deep(strong) {
  font-weight: 600;
}

.markdown-content :deep(em) {
  font-style: italic;
}
</style>
