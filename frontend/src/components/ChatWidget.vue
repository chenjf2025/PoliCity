<template>
  <div class="chat-container">
    <div v-if="chatVisible" class="chat-window">
      <div class="chat-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>AI智能助手</span>
          <el-icon @click="chatVisible = false" style="cursor: pointer;"><Close /></el-icon>
        </div>
      </div>

      <div ref="messagesRef" class="chat-messages">
        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
          <div class="message-content">
            <div v-if="msg.role === 'user'" class="user-message">{{ msg.content }}</div>
            <div v-else class="markdown-content" v-html="renderMarkdown(msg.content)"></div>
          </div>
        </div>
        <div v-if="loading" class="message assistant">
          <div class="message-content">
            <div class="markdown-content"><el-icon class="is-loading"><Loading /></el-icon> 思考中...</div>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="inputMessage"
          placeholder="输入您的问题..."
          @keyup.enter="sendMessage"
          :disabled="loading"
        />
        <el-button type="primary" @click="sendMessage" :loading="loading">
          发送
        </el-button>
      </div>
    </div>

    <div v-if="!chatVisible" class="chat-toggle" @click="chatVisible = true">
      <el-icon :size="28"><ChatDotRound /></el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { difyAPI } from '../api'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const chatVisible = ref(false)
const inputMessage = ref('')
const messages = ref<Message[]>([
  {
    role: 'assistant',
    content: '您好！我是城策AI助手，可以帮您分析城市发展状况、解读评价指标、解答政策问题。请问有什么可以帮您？'
  }
])
const loading = ref(false)
const messagesRef = ref<HTMLElement>()

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
    content: query
  })

  scrollToBottom()
  loading.value = true

  try {
    const response = await difyAPI.chat({
      query,
      user_id: 'web_user'
    })

    messages.value.push({
      role: 'assistant',
      content: response.answer || '抱歉，我现在无法回答这个问题。'
    })
  } catch (error: any) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后再试。'
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.message {
  margin-bottom: 12px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.user-message {
  white-space: pre-wrap;
}

.message.user .message-content {
  background: #409eff;
  color: white;
  border-bottom-right-radius: 2px;
}

.message.assistant .message-content {
  background: #f4f4f5;
  color: #303133;
  border-bottom-left-radius: 2px;
}

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
</style>
