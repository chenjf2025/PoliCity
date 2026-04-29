<template>
  <div class="benchmark-page">
    <div class="dashboard-card">
      <div class="card-title">对标分析</div>

      <!-- 对标配置 -->
      <el-form :inline="true" style="margin-bottom: 20px;">
        <el-form-item label="区域">
          <el-select v-model="regionCode">
            <el-option label="默认城市" value="default" />
          </el-select>
        </el-form-item>
        <el-form-item label="年份">
          <el-select v-model="reportYear">
            <el-option v-for="y in [2020,2021,2022,2023,2024,2025]" :key="y" :label="y" :value="y" />
          </el-select>
        </el-form-item>
        <el-form-item label="对标城市">
          <el-select v-model="selectedCities" multiple placeholder="选择对标城市" style="width: 300px;">
            <el-option
              v-for="city in availableCities"
              :key="city.city_code"
              :label="city.city_name"
              :value="city.city_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="runCompare">开始对比</el-button>
        </el-form-item>
      </el-form>

      <!-- 对标结果 -->
      <div v-if="compareResult">
        <el-row :gutter="20">
          <!-- 雷达图对比 -->
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>雷达图对比</span>
              </template>
              <RadarChart
                v-if="compareResult.self_analysis?.radar"
                :dimensions="compareResult.self_analysis.radar.dimensions"
                :comparison-data="compareResult.benchmark_cities?.[0]?.dimensions"
                :comparison-name="compareResult.benchmark_cities?.[0]?.city_name"
              />
            </el-card>
          </el-col>

          <!-- 总分对比 -->
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>总分排名</span>
              </template>
              <div class="ranking-list">
                <div
                  v-for="(item, idx) in compareResult.rankings"
                  :key="idx"
                  :class="['ranking-item', item.city_code === regionCode ? 'highlight' : '']"
                >
                  <span class="rank">{{ idx + 1 }}</span>
                  <span class="city">{{ item.city_name }}</span>
                  <span class="score">{{ item.total_score?.toFixed(1) || '--' }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 竞争劣势 -->
        <el-card shadow="hover" style="margin-top: 20px;">
          <template #header>
            <span>竞争劣势分析</span>
          </template>
          <el-table :data="compareResult.competitive_weaknesses" stripe>
            <el-table-column prop="dimension" label="维度" />
            <el-table-column prop="self_score" label="本市得分" />
            <el-table-column prop="benchmark_score" label="对标得分" />
            <el-table-column prop="gap" label="差距">
              <template #default="{ row }">
                <span style="color: #f56c6c;">-{{ row.gap }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="benchmark_city" label="对标城市" />
          </el-table>
          <el-empty v-if="!compareResult.competitive_weaknesses?.length" description="暂无明显竞争劣势" />
        </el-card>
      </div>

      <el-empty v-else description="请选择对标城市开始对比分析" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { benchmarkAPI } from '../api'
import RadarChart from '../components/RadarChart.vue'

const regionCode = ref('default')
const reportYear = ref(2024)
const selectedCities = ref<string[]>([])
const availableCities = ref<any[]>([])
const compareResult = ref<any>(null)

const loadCities = async () => {
  try {
    const res = await benchmarkAPI.listCities()
    availableCities.value = res.cities || []
  } catch (error) {
    console.error('加载城市列表失败:', error)
  }
}

const runCompare = async () => {
  if (!selectedCities.value.length) {
    return
  }

  try {
    compareResult.value = await benchmarkAPI.compare({
      region_code: regionCode.value,
      region_name: '默认城市',
      benchmark_city_codes: selectedCities.value,
      report_year: reportYear.value
    })
  } catch (error) {
    console.error('对比分析失败:', error)
  }
}

onMounted(() => {
  loadCities()
})
</script>

<style scoped>
.ranking-list {
  padding: 10px 0;
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.ranking-item.highlight {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}

.ranking-item .rank {
  width: 30px;
  height: 30px;
  line-height: 30px;
  text-align: center;
  background: #909399;
  color: white;
  border-radius: 50%;
  margin-right: 16px;
  font-weight: bold;
}

.ranking-item:nth-child(1) .rank {
  background: #ffd700;
}

.ranking-item:nth-child(2) .rank {
  background: #c0c0c0;
}

.ranking-item:nth-child(3) .rank {
  background: #cd7f32;
}

.ranking-item .city {
  flex: 1;
  font-weight: 500;
}

.ranking-item .score {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

:deep(.el-select) {
  width: 150px;
}

:deep(.el-select .el-input__inner) {
  width: 150px;
}
</style>
