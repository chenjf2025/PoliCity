<template>
  <div class="evaluation-page">
    <div class="dashboard-card">
      <div class="card-title">评价详情</div>

      <!-- 选择器 -->
      <el-form :inline="true" style="margin-bottom: 20px;">
        <el-form-item label="区域">
          <el-select v-model="regionCode" @change="loadEvaluation">
            <el-option v-for="city in cities" :key="city.city_code" :label="city.city_name" :value="city.city_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="年份">
          <el-select v-model="reportYear" @change="loadEvaluation">
            <el-option v-for="y in [2020,2021,2022,2023,2024,2025]" :key="y" :label="y" :value="y" />
          </el-select>
        </el-form-item>
      </el-form>

      <!-- 五维度详情 -->
      <el-row :gutter="20">
        <el-col v-for="dim in dimensionDetail" :key="dim.code" :span="8" style="margin-bottom: 20px;">
          <el-card shadow="hover">
            <template #header>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ dim.dimension_cn }}</span>
                <el-tag type="primary">{{ dim.overall_score || '--' }}分</el-tag>
              </div>
            </template>
            <el-progress
              :percentage="getPercentage(dim.overall_score)"
              :color="getProgressColor(dim.overall_score)"
            />
            <el-divider />
            <div v-for="ind in dim.indicators?.slice(0, 5)" :key="ind.code" class="indicator-item">
              <span>{{ ind.name }}</span>
              <el-tag :type="getScoreType(ind.score)" size="small">{{ ind.score }}</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 趋势图 -->
      <div class="dashboard-card" style="margin-top: 20px;">
        <div class="card-title">历年趋势</div>
        <div ref="trendChartRef" style="height: 300px;"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { evaluationAPI, benchmarkAPI } from '../api'
import * as echarts from 'echarts'

const regionCode = ref('default')
const reportYear = ref(2024)
const cities = ref<any[]>([])
const dimensionDetail = ref<any[]>([])
const trendData = ref<any[]>([])
const trendChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null

const dimensions = ['economic', 'culture', 'human', 'urban', 'governance']

const loadEvaluation = async () => {
  try {
    // 加载各维度详情
    const promises = dimensions.map(d =>
      evaluationAPI.getDimensionDetail(d, regionCode.value, reportYear.value)
    )
    dimensionDetail.value = await Promise.all(promises)

    // 加载趋势数据
    const trendRes = await evaluationAPI.getTrend(regionCode.value, 5)
    trendData.value = trendRes.trend || []
    nextTick(() => initTrendChart())
  } catch (error) {
    console.error('加载评价详情失败:', error)
  }
}

const getProgressColor = (score: number) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getScoreType = (score: number) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

const getPercentage = (score: any) => {
  const s = Number(score) || 0
  return Math.min(100, Math.max(0, Math.round(s)))
}

const initTrendChart = () => {
  if (!trendChartRef.value || !trendData.value.length) return

  if (trendChart) trendChart.dispose()

  trendChart = echarts.init(trendChartRef.value)

  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['总分', '经济', '文化', '人力', '城乡', '治理']
    },
    xAxis: {
      type: 'category',
      data: trendData.value.map(t => t.report_year)
    },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: [
      { name: '总分', type: 'line', data: trendData.value.map(t => t.total_score) },
      { name: '经济', type: 'line', data: trendData.value.map(t => t.economic_score) },
      { name: '文化', type: 'line', data: trendData.value.map(t => t.culture_score) },
      { name: '人力', type: 'line', data: trendData.value.map(t => t.human_score) },
      { name: '城乡', type: 'line', data: trendData.value.map(t => t.urban_score) },
      { name: '治理', type: 'line', data: trendData.value.map(t => t.governance_score) }
    ]
  }

  trendChart.setOption(option)
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
  loadEvaluation()
})
</script>

<style scoped>
.indicator-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}

:deep(.el-select) {
  width: 150px;
}

:deep(.el-select .el-input__inner) {
  width: 150px;
}
</style>
