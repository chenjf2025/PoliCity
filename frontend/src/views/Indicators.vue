<template>
  <div class="indicators-page">
    <div class="dashboard-card">
      <div class="card-title">指标管理</div>

      <!-- 工具栏 -->
      <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center;">
        <el-button type="primary" @click="showImportDialog = true">
          <el-icon><Upload /></el-icon> 导入数据
        </el-button>
        <el-button type="success" @click="triggerNormalize">
          <el-icon><Refresh /></el-icon> 触发标准化计算
        </el-button>
        <el-select v-model="selectedDimension" placeholder="按维度筛选" clearable style="width: 150px;">
          <el-option label="全部" value="" />
          <el-option label="经济活力" value="economic" />
          <el-option label="文化繁荣" value="culture" />
          <el-option label="人力资源" value="human" />
          <el-option label="城乡融合" value="urban" />
          <el-option label="城市治理" value="governance" />
        </el-select>
      </div>

      <!-- 维度汇总 -->
      <el-row :gutter="20" style="margin-bottom: 20px;">
        <el-col v-for="dim in dimensionSummary" :key="dim.dimension" :span="4">
          <el-card shadow="hover">
            <div style="text-align: center;">
              <div style="font-size: 24px; font-weight: bold; color: #409eff;">{{ dim.indicator_count }}</div>
              <div style="font-size: 12px; color: #909399;">{{ dim.dimension_cn }}</div>
              <div style="font-size: 12px; color: #67c23a;">权重{{ (dim.weight * 100).toFixed(0) }}%</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 指标表格 -->
      <el-table :data="filteredIndicators" stripe style="width: 100%">
        <el-table-column prop="indicator_code" label="编码" width="100" />
        <el-table-column prop="indicator_name" label="指标名称" />
        <el-table-column prop="dimension_cn" label="维度" width="120" />
        <el-table-column prop="weight" label="权重" width="80">
          <template #default="{ row }">
            {{ (row.weight * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column prop="polarity" label="极性" width="80">
          <template #default="{ row }">
            <el-tag :type="row.polarity === 1 ? 'success' : 'danger'">
              {{ row.polarity === 1 ? '正向' : '负向' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="100" />
        <el-table-column prop="data_source" label="数据来源" width="120" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '生效' : '废弃' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 导入对话框 -->
    <el-dialog v-model="showImportDialog" title="导入原始数据" width="500px">
      <el-form>
        <el-form-item label="报告年份">
          <el-select v-model="importYear" style="width: 100%;">
            <el-option v-for="y in [2020,2021,2022,2023,2024,2025]" :key="y" :label="y" :value="y" />
          </el-select>
        </el-form-item>
        <el-form-item label="Excel文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls,.csv"
            :on-change="handleFileChange"
          >
            <el-button>选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="importData" :loading="importing">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { indicatorAPI, dataAPI } from '../api'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'

const indicators = ref<any[]>([])
const dimensionSummary = ref<any[]>([])
const selectedDimension = ref('')
const showImportDialog = ref(false)
const importYear = ref(2024)
const importFile = ref<UploadFile | null>(null)
const importing = ref(false)
const uploadRef = ref()

const filteredIndicators = computed(() => {
  if (!selectedDimension.value) return indicators.value
  return indicators.value.filter(i => i.dimension === selectedDimension.value)
})

const loadIndicators = async () => {
  try {
    indicators.value = await indicatorAPI.list()
    dimensionSummary.value = await indicatorAPI.getDimensions()
  } catch (error) {
    console.error('加载指标失败:', error)
  }
}

const handleFileChange = (file: UploadFile) => {
  console.log('File selected:', file)
  importFile.value = file
}

const importData = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择文件')
    return
  }

  importing.value = true
  try {
    const formData = new FormData()
    // el-upload 的 file.raw 是原始文件对象
    const fileToUpload = importFile.value.raw || importFile.value
    formData.append('file', fileToUpload)

    console.log('Uploading file:', importFile.value.name, fileToUpload)

    const response = await dataAPI.importExcel(formData, importYear.value)
    ElMessage.success(`导入成功！共导入 ${response.imported_count} 条数据`)
    showImportDialog.value = false
    importFile.value = null
    uploadRef.value?.clearFiles()
  } catch (error: any) {
    console.error('导入失败:', error)
    let errorMsg = '导入失败'
    if (error?.response?.data) {
      const data = error.response.data
      if (typeof data === 'string') {
        errorMsg = data
      } else if (Array.isArray(data.detail)) {
        // FastAPI 验证错误数组
        errorMsg = data.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
      } else if (data.detail) {
        errorMsg = String(data.detail)
      } else if (data.message) {
        errorMsg = data.message
      } else {
        errorMsg = JSON.stringify(data)
      }
    } else if (error?.message) {
      errorMsg = error.message
    }
    ElMessage.error(`导入失败: ${errorMsg}`)
  } finally {
    importing.value = false
  }
}

const triggerNormalize = async () => {
  try {
    await dataAPI.normalize(importYear.value)
    ElMessage.success('标准化计算完成')
  } catch (error) {
    ElMessage.error('标准化计算失败')
  }
}

onMounted(() => {
  loadIndicators()
})
</script>
