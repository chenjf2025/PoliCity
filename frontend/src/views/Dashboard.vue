<template>
  <div class="dashboard">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <div class="dashboard-card source-tooltip" v-if="radarData.source">
          <el-tooltip :content="`来源: ${radarData.source.source_name}${radarData.source.source_url ? '<br/>链接: ' + radarData.source.source_url : ''}`" raw-content>
            <div>
              <div class="stat-number">{{ radarData.total_score || '--' }}</div>
              <div class="stat-label">综合发展指数 <el-icon><QuestionFilled /></el-icon></div>
            </div>
          </el-tooltip>
        </div>
        <div class="dashboard-card" v-else>
          <div class="stat-number">{{ radarData.total_score || '--' }}</div>
          <div class="stat-label">综合发展指数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="dashboard-card source-tooltip" v-if="radarData.source">
          <el-tooltip :content="`来源: ${radarData.source.source_name}${radarData.source.source_url ? '<br/>链接: ' + radarData.source.source_url : ''}`" raw-content>
            <div>
              <div class="stat-number success">{{ radarData.dimensions?.[0]?.score || '--' }}</div>
              <div class="stat-label">经济活力得分 <el-icon><QuestionFilled /></el-icon></div>
            </div>
          </el-tooltip>
        </div>
        <div class="dashboard-card" v-else>
          <div class="stat-number success">{{ radarData.dimensions?.[0]?.score || '--' }}</div>
          <div class="stat-label">经济活力得分</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="dashboard-card source-tooltip" v-if="radarData.source">
          <el-tooltip :content="`来源: ${radarData.source.source_name}${radarData.source.source_url ? '<br/>链接: ' + radarData.source.source_url : ''}`" raw-content>
            <div>
              <div class="stat-number warning">{{ radarData.dimensions?.[1]?.score || '--' }}</div>
              <div class="stat-label">文化繁荣得分 <el-icon><QuestionFilled /></el-icon></div>
            </div>
          </el-tooltip>
        </div>
        <div class="dashboard-card" v-else>
          <div class="stat-number warning">{{ radarData.dimensions?.[1]?.score || '--' }}</div>
          <div class="stat-label">文化繁荣得分</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="dashboard-card source-tooltip" v-if="radarData.source">
          <el-tooltip :content="`来源: ${radarData.source.source_name}${radarData.source.source_url ? '<br/>链接: ' + radarData.source.source_url : ''}`" raw-content>
            <div>
              <div class="stat-number danger">{{ shortboardCount }}</div>
              <div class="stat-label">待改进指标 <el-icon><QuestionFilled /></el-icon></div>
            </div>
          </el-tooltip>
        </div>
        <div class="dashboard-card" v-else>
          <div class="stat-number danger">{{ shortboardCount }}</div>
          <div class="stat-label">待改进指标</div>
        </div>
      </el-col>
    </el-row>

    <!-- 主内容区 -->
    <el-row :gutter="20">
      <!-- 雷达图 -->
      <el-col :span="12">
        <div class="dashboard-card">
          <div class="card-title">六维发展雷达图</div>
          <RadarChart
            v-if="radarData.dimensions?.length"
            :dimensions="radarData.dimensions"
            :source-info="radarData.source"
          />
          <el-empty v-else description="暂无数据" />
        </div>
      </el-col>

      <!-- 右侧信息 -->
      <el-col :span="12">
        <!-- 区域选择 -->
        <div class="dashboard-card" style="margin-bottom: 20px;">
          <div class="card-title">区域选择</div>
          <el-form :inline="true">
            <el-form-item label="区域">
              <el-select v-model="regionCode" placeholder="请选择区域" @change="loadData">
                <el-option v-for="city in cities" :key="city.city_code" :label="city.city_name" :value="city.city_code" />
              </el-select>
            </el-form-item>
            <el-form-item label="年份">
              <el-select v-model="reportYear" placeholder="请选择年份" @change="loadData">
                <el-option v-for="y in years" :key="y" :label="y" :value="y" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 排名信息 -->
        <div class="dashboard-card" style="margin-bottom: 20px;">
          <div class="card-title">排名信息</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="城市排名">
              {{ totalData.city_rank || '--' }} / {{ totalData.total_cities || '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="总分">{{ totalData.total_score || '--' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 短板预警 -->
        <div class="dashboard-card">
          <div class="card-title">短板预警</div>
          <el-alert
            v-for="(item, idx) in shortboards.slice(0, 5)"
            :key="idx"
            :title="`${item.indicator_name}: ${(item.score ?? item.gap ?? 0).toFixed(1)}分`"
            type="warning"
            :closable="false"
            style="margin-bottom: 8px;"
          />
          <el-empty v-if="!shortboards.length" description="暂无短板预警" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { evaluationAPI, benchmarkAPI } from '../api'
import { QuestionFilled } from '@element-plus/icons-vue'
import RadarChart from '../components/RadarChart.vue'

const regionCode = ref('default')
const reportYear = ref(2024)
const years = [2020, 2021, 2022, 2023, 2024, 2025]
const cities = ref<any[]>([])

const radarData = ref<any>({
  dimensions: [],
  total_score: 0
})

const totalData = ref<any>({})

const shortboards = ref<any[]>([])
const shortboardCount = ref(0)

const loadData = async () => {
  try {
    // 获取雷达图数据
    radarData.value = await evaluationAPI.getRadar(regionCode.value, reportYear.value)

    // 获取总分和排名
    totalData.value = await evaluationAPI.getTotal(regionCode.value, reportYear.value)

    // 获取短板预警
    const shortboardRes = await evaluationAPI.getShortboard(regionCode.value, reportYear.value)
    shortboards.value = shortboardRes.shortboards || []
    shortboardCount.value = shortboardRes.shortboard_count || 0
  } catch (error) {
    console.error('加载数据失败:', error)
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
  loadData()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

:deep(.el-select) {
  width: 150px;
}

:deep(.el-select .el-input__inner) {
  width: 150px;
}

.source-tooltip {
  cursor: pointer;
}

.source-tooltip .el-icon {
  margin-left: 4px;
  font-size: 12px;
  vertical-align: middle;
}

.stat-label {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
