<template>
  <div class="simulation-page">
    <div class="dashboard-card">
      <div class="card-title">政策仿真模拟器</div>

      <!-- 仿真配置 -->
      <el-form :inline="true" style="margin-bottom: 20px;">
        <el-form-item label="区域">
          <el-select v-model="regionCode" @change="loadSliders">
            <el-option v-for="city in cities" :key="city.city_code" :label="city.city_name" :value="city.city_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="年份">
          <el-select v-model="reportYear" @change="loadSliders">
            <el-option v-for="y in [2020,2021,2022,2023,2024,2025]" :key="y" :label="y" :value="y" />
          </el-select>
        </el-form-item>
      </el-form>

      <!-- 指标滑块 -->
      <el-card shadow="hover" style="margin-bottom: 20px;">
        <template #header>
          <span>调整指标（拖动滑块模拟政策变化）</span>
        </template>

        <div v-for="(slider, idx) in sliders" :key="idx" class="simulation-slider">
          <div class="slider-label">
            <span>{{ slider.name }}</span>
            <span class="slider-value">{{ slider.currentValue }} {{ slider.unit }}</span>
          </div>
          <el-slider
            v-model="slider.currentValue"
            :min="slider.min"
            :max="slider.max"
            :step="slider.step"
            :format-tooltip="(v: number) => v.toFixed(2)"
            @change="updateSimulation(idx)"
          />
        </div>
      </el-card>

      <!-- 仿真结果 -->
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>仿真结果</span>
            </template>
            <div v-if="simulationResult">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="原始总分">
                  {{ simulationResult.original_scores?.total_score || '--' }}
                </el-descriptions-item>
                <el-descriptions-item label="仿真后总分">
                  <span style="color: #67c23a; font-weight: bold;">
                    {{ simulationResult.simulated_scores?.total_score || '--' }}
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="变化量">
                  <span :style="{ color: simulationResult.score_delta >= 0 ? '#67c23a' : '#f56c6c' }">
                    {{ simulationResult.score_delta >= 0 ? '+' : '' }}{{ simulationResult.score_delta || 0 }}
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="变化率">
                  {{ simulationResult.score_change_percent || 0 }}%
                </el-descriptions-item>
              </el-descriptions>

              <el-divider>维度变化</el-divider>
              <div v-for="(dim, idx) in simulationResult.changed_dimensions" :key="idx" class="dimension-change">
                <span>{{ dim.dimension }}</span>
                <span>{{ dim.original }} → {{ dim.simulated }}</span>
                <span :style="{ color: dim.delta >= 0 ? '#67c23a' : '#f56c6c' }">
                  ({{ dim.delta >= 0 ? '+' : '' }}{{ dim.delta }})
                </span>
              </div>
            </div>
            <el-empty v-else description="请调整滑块开始仿真" />
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>Agent智能分析</span>
              <div style="float: right; display: flex; gap: 8px;">
                <el-button v-if="streamingContent || agentResult?.llm_analysis || agentResult?.policy_analysis" size="small" type="success" @click="exportPdf">
                  导出PDF
                </el-button>
                <el-button size="small" type="primary" @click="runAgentAnalysis" :disabled="isStreaming">
                  {{ isStreaming ? '分析中...' : '启动分析' }}
                </el-button>
              </div>
            </template>
            <div v-if="streamingContent || agentResult">
              <!-- 流式内容显示 -->
              <div v-if="streamingContent" class="markdown-content" v-html="renderMarkdown(streamingContent)"></div>
              <!-- 非流式完整结果 -->
              <div v-else-if="agentResult.llm_analysis" class="markdown-content" v-html="renderMarkdown(agentResult.llm_analysis)"></div>
              <template v-else>
                <el-divider content-position="left">关键洞察</el-divider>
                <ul>
                  <li v-for="(insight, idx) in agentResult.policy_analysis?.insights || agentResult.insights || []" :key="idx">
                    {{ insight }}
                  </li>
                </ul>
                <el-divider content-position="left">政策建议</el-divider>
                <ul>
                  <li v-for="(rec, idx) in agentResult.policy_analysis?.recommendations || agentResult.recommendations || []" :key="idx">
                    {{ rec }}
                  </li>
                </ul>
              </template>
            </div>
            <el-empty v-else description="点击启动分析获取AI建议" />
          </el-card>
        </el-col>
      </el-row>

      <!-- 历史仿真 -->
      <el-card shadow="hover" style="margin-top: 20px;">
        <template #header>
          <span>历史仿真记录</span>
        </template>
        <el-table :data="simulationHistory" stripe>
          <el-table-column prop="created_at" label="时间" width="160" />
          <el-table-column prop="simulation_name" label="仿真名称" />
          <el-table-column prop="original_total_score" label="原始总分" width="100" />
          <el-table-column prop="simulated_total_score" label="仿真总分" width="100" />
          <el-table-column prop="score_delta" label="变化量" width="80">
            <template #default="{ row }">
              <span :style="{ color: row.score_delta >= 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.score_delta >= 0 ? '+' : '' }}{{ row.score_delta }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="分析报告" width="100">
            <template #default="{ row }">
              <el-button v-if="row.analysis_report" type="primary" link @click="viewReport(row)">查看</el-button>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 分析报告对话框 -->
      <el-dialog v-model="reportDialogVisible" title="分析报告" width="700px" destroy-on-close>
        <div v-if="currentReport" class="report-content" v-html="renderMarkdown(currentReport)"></div>
        <template #footer>
          <el-button @click="reportDialogVisible = false">关闭</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { simulationAPI, dataAPI, benchmarkAPI } from '../api'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import html2pdf from 'html2pdf.js'

const regionCode = ref('default')
const reportYear = ref(2024)
const cities = ref<any[]>([])

interface Slider {
  indicator_code: string
  name: string
  unit: string
  min: number
  max: number
  step: number
  currentValue: number
  originalValue: number
}

const sliders = ref<Slider[]>([])
const simulationResult = ref<any>(null)
const agentResult = ref<any>(null)
const simulationHistory = ref<any[]>([])
const reportDialogVisible = ref(false)
const currentReport = ref('')
const streamingContent = ref('')
const isStreaming = ref(false)

const renderMarkdown = (content: string): string => {
  if (!content) return ''
  return marked.parse(content) as string
}

const viewReport = (row: any) => {
  currentReport.value = row.analysis_report || ''
  reportDialogVisible.value = true
}

const exportPdf = async () => {
  if (!agentResult.value) {
    ElMessage.warning('请先运行分析')
    return
  }

  try {
    const content = agentResult.value.llm_analysis || agentResult.value.policy_analysis?.recommendations?.join('\n') || ''
    const htmlContent = renderMarkdown(content)

    const element = document.createElement('div')
    element.innerHTML = htmlContent
    element.style.padding = '20px'
    element.style.fontFamily = 'Arial, sans-serif'
    element.style.lineHeight = '1.6'

    const opt = {
      margin: 10,
      filename: `政策仿真分析报告_${Date.now()}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    }

    await html2pdf().set(opt).from(element).save()
    ElMessage.success('PDF导出成功')
  } catch (error) {
    console.error('PDF导出失败:', error)
    ElMessage.error('PDF导出失败')
  }
}

const loadSliders = async () => {
  try {
    // 获取经济维度指标作为示例
    const res = await dataAPI.getStandardScores(regionCode.value, reportYear.value)
    const scores = res.scores || []

    // 选取部分指标创建滑块
    const selectedCodes = ['E01', 'E05', 'E06', 'H04', 'G04']

    sliders.value = selectedCodes.map(code => {
      const score = scores.find((s: any) => s.indicator_code === code)
      const value = score?.raw_value || 50

      return {
        indicator_code: code,
        name: getIndicatorName(code),
        unit: getIndicatorUnit(code),
        min: value * 0.5,
        max: value * 1.5,
        step: value * 0.01,
        currentValue: value,
        originalValue: value
      }
    })
  } catch (error) {
    console.error('加载滑块失败:', error)
  }
}

const getIndicatorName = (code: string): string => {
  const names: Record<string, string> = {
    'E01': '人均地区生产总值',
    'E05': 'R&D经费投入强度',
    'E06': '万人发明专利拥有量',
    'H04': '净流入大学生数',
    'G04': '空气质量优良天数'
  }
  return names[code] || code
}

const getIndicatorUnit = (code: string): string => {
  const units: Record<string, string> = {
    'E01': '万元',
    'E05': '%',
    'E06': '件/万人',
    'H04': '人',
    'G04': '%'
  }
  return units[code] || ''
}

const updateSimulation = async (idx: number) => {
  const slider = sliders.value[idx]
  const selfCity = cities.value.find(c => c.city_code === regionCode.value)

  try {
    const result = await simulationAPI.whatIf({
      region_code: regionCode.value,
      region_name: selfCity?.city_name || regionCode.value,
      report_year: reportYear.value,
      simulation_params: sliders.value.map(s => ({
        indicator_code: s.indicator_code,
        simulated_value: s.currentValue
      }))
    })

    simulationResult.value = result
  } catch (error) {
    console.error('仿真计算失败:', error)
  }
}

const runAgentAnalysis = async () => {
  const selfCity = cities.value.find(c => c.city_code === regionCode.value)

  isStreaming.value = true
  streamingContent.value = ''
  agentResult.value = null

  try {
    const response = await simulationAPI.agentAnalyzeStream({
      region_code: regionCode.value,
      region_name: selfCity?.city_name || regionCode.value,
      report_year: reportYear.value,
      policy_changes: sliders.value.map(s => ({
        indicator_code: s.indicator_code,
        change_percent: ((s.currentValue - s.originalValue) / s.originalValue) * 100
      }))
    }) as Response

    console.log('Response status:', response.status)
    console.log('Response ok:', response.ok)

    if (!response.ok) {
      throw new Error('分析请求失败')
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法读取响应流')
    }

    const decoder = new TextDecoder()
    let buffer = ''
    let receivedData = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk

      // 持续处理buffer中的所有完整事件
      while (buffer.includes('\n\n')) {
        const eventEnd = buffer.indexOf('\n\n')
        const eventData = buffer.slice(0, eventEnd)
        buffer = buffer.slice(eventEnd + 2)

        // 解析SSE数据行
        const lines = eventData.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            try {
              const parsed = JSON.parse(data)
              console.log('Parsed event:', parsed.type)
              if (parsed.type === 'content' && parsed.content) {
                streamingContent.value += parsed.content
                receivedData = true
              } else if (parsed.type === 'done') {
                isStreaming.value = false
                // 将流式内容设置为agentResult
                agentResult.value = {
                  llm_analysis: streamingContent.value
                }
                loadHistory()
                ElMessage.success('Agent分析完成')
              }
            } catch (e) {
              console.error('Parse error:', e)
            }
          }
        }
      }
    }

    // 处理剩余buffer
    if (buffer.startsWith('data: ')) {
      const data = buffer.slice(6)
      try {
        const parsed = JSON.parse(data)
        if (parsed.type === 'content' && parsed.content) {
          streamingContent.value += parsed.content
        }
      } catch (e) {
        console.error('Final parse error:', e)
      }
    }

    console.log('Stream ended, receivedData:', receivedData)
    if (!receivedData && !isStreaming.value) {
      // 如果没有收到数据且流已结束，可能出错了
    }
  } catch (error) {
    console.error('Agent分析失败:', error)
    ElMessage.error('Agent分析失败: ' + (error as Error).message)
    isStreaming.value = false
  }
}

const loadHistory = async () => {
  try {
    const res = await simulationAPI.getHistory({ limit: 10 })
    console.log('历史记录响应:', res)
    console.log('历史记录数量:', res.count, '列表长度:', res.history?.length)
    simulationHistory.value = res.history || []
  } catch (error) {
    console.error('加载历史失败:', error)
  }
}

onMounted(async () => {
  try {
    const res = await benchmarkAPI.listCities()
    cities.value = res.cities || []
    if (cities.value.length > 0) {
      regionCode.value = cities.value[0].city_code
    }
  } catch (e) {
    console.error('加载城市列表失败', e)
  }
  loadSliders()
  loadHistory()
})
</script>

<style scoped>
.dimension-change {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 14px;
}

.markdown-content {
  font-size: 14px;
  line-height: 1.6;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin-top: 12px;
  margin-bottom: 8px;
}

.markdown-content :deep(p) {
  margin: 8px 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 20px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(strong) {
  color: #409eff;
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
}

:deep(.el-select) {
  width: 150px;
}

:deep(.el-select .el-input__inner) {
  width: 150px;
}

.report-content {
  max-height: 500px;
  overflow-y: auto;
  line-height: 1.6;
}

.report-content h2 {
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
  margin-top: 16px;
}

.report-content h3 {
  color: #409eff;
  margin-top: 12px;
}

.report-content ul {
  padding-left: 20px;
}

.report-content li {
  margin: 8px 0;
}
</style>
