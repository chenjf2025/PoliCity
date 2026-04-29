<template>
  <div class="chat-page">
    <div class="dashboard-card">
      <div class="card-title">AI智能助手</div>

      <div class="chat-container-full">
        <div ref="messagesRef" class="messages-list">
          <div v-for="(msg, idx) in messages" :key="idx" :class="['message-item', msg.role]">
            <div class="avatar">
              <el-icon v-if="msg.role === 'user'" :size="24"><User /></el-icon>
              <el-icon v-else :size="24"><Robot /></el-icon>
            </div>
            <div class="content">
              <div class="message-text">
                <div v-if="msg.role === 'user'" class="user-text">{{ msg.content }}</div>
                <div v-else class="markdown-content" v-html="renderMarkdown(msg.content)"></div>
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
            <el-button type="primary" @click="sendMessage" :loading="loading">
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { difyChatStream } from '../api'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
  time: string
}

const messages = ref<Message[]>([
  {
    role: 'assistant',
    content: '您好！我是城策AI助手。我可以帮您：\n1. 分析城市发展状况和评价指标\n2. 解读雷达图和短板指标\n3. 解答政策仿真相关问题\n4. 提供城市治理建议\n\n请问有什么可以帮助您？',
    time: new Date().toLocaleTimeString()
  }
])

const inputMessage = ref('')
const loading = ref(false)
const messagesRef = ref<HTMLElement>()
const currentAssistantMsg = ref<Message | null>(null)

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

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const query = inputMessage.value.trim()
  inputMessage.value = ''

  messages.value.push({
    role: 'user',
    content: query,
    time: new Date().toLocaleTimeString()
  })
  scrollToBottom()

  loading.value = true

  // 创建空的助手消息用于流式更新
  currentAssistantMsg.value = {
    role: 'assistant',
    content: '',
    time: new Date().toLocaleTimeString()
  }
  messages.value.push(currentAssistantMsg.value)

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

      // 处理SSE数据
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            // 处理Dify流式返回的不同事件类型
            if (data.event === 'message' || data.event === 'assistant' || data.event === 'agent_message') {
              const contentChunk = data.answer || data.content || data.message || ''
              if (contentChunk && currentAssistantMsg.value) {
                currentAssistantMsg.value.content += contentChunk
                scrollToBottom()
              }
            } else if (data.event === 'message_end') {
              // 消息结束
              loading.value = false
            } else if (data.event === 'error' || data.error) {
              console.error('Stream error:', data.error || data.message)
              loading.value = false
            }
          } catch (e) {
            // 忽略解析错误，继续处理下一条
          }
        }
      }
    }

    // 确保loading关闭
    loading.value = false

    // 如果没有收到任何内容
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
</script>

<style scoped>
.chat-container-full {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 280px);
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

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  text-align: right;
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
