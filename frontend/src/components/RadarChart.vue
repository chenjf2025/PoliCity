<template>
  <div ref="chartRef" class="radar-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

interface Dimension {
  name: string
  code: string
  score: number
  weight: number
}

interface BenchmarkCityData {
  dimensions: Dimension[]
  city_name: string
  city_code: string
}

interface Props {
  dimensions: Dimension[]
  comparisonData?: BenchmarkCityData[]
  sourceInfo?: {
    source_name?: string
    source_url?: string
  }
}

const props = defineProps<Props>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const COLORS = ['#fa8c16', '#52c41a', '#eb2f96', '#722ed1', '#13c2c2', '#faad14']

const initChart = () => {
  if (!chartRef.value) return

  if (chart) {
    chart.dispose()
  }
  chart = echarts.init(chartRef.value)

  const indicator = props.dimensions.map(d => ({
    name: d.name,
    max: 100
  }))

  const data = props.dimensions.map(d => d.score || 0)

  const series: any[] = [
    {
      value: data,
      name: '当前城市',
      type: 'radar',
      lineStyle: { width: 2 },
      areaStyle: { opacity: 0.3 },
      itemStyle: { color: '#5470c6' }
    }
  ]

  if (props.comparisonData && props.comparisonData.length > 0) {
    props.comparisonData.forEach((city, idx) => {
      series.push({
        value: city.dimensions.map(d => d.score || 0),
        name: city.city_name,
        type: 'radar',
        lineStyle: { width: 2, type: idx % 2 === 0 ? 'dashed' : 'dotted' },
        areaStyle: { opacity: 0.1 },
        itemStyle: { color: COLORS[idx % COLORS.length] }
      })
    })
  }

  const option = {
    title: {
      text: '六维评价雷达图',
      left: 'center',
      top: 10
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        // params[0] 包含当前悬停的指标信息
        const param = params[0];
        if (!param) return '';

        // radar axis tooltip: name 是指标名称, dataIndex 是指标索引
        const dimIdx = param.dataIndex;
        const dim = dimIdx >= 0 && dimIdx < props.dimensions.length ? props.dimensions[dimIdx] : props.dimensions[0];

        // 构建所有 series 在该指标上的得分
        let html = `<strong>${dim.name}</strong><br/>`;
        params.forEach((p: any) => {
          const score = typeof p.value === 'number' ? p.value : (Array.isArray(p.value) ? p.value[0] : 0);
          html += `${p.marker} ${p.seriesName}: ${score}分<br/>`;
        });

        // 显示权重和来源
        html += `<br/>(权重: ${(dim.weight * 100).toFixed(0)}%)`;
        if (props.sourceInfo) {
          html += `<br/>来源: ${props.sourceInfo.source_name || '-'}`;
          if (props.sourceInfo.source_url) {
            html += `<br/><a href="${props.sourceInfo.source_url}" target="_blank" style="color:#409eff">点击查看来源</a>`;
          }
        }
        return html;
      }
    },
    legend: {
      data: series.map(s => s.name),
      bottom: 10
    },
    radar: {
      indicator,
      center: ['50%', '55%'],
      radius: '60%'
    },
    series: [{
      type: 'radar',
      data: series
    }]
  }

  chart.setOption(option)
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => chart?.resize())
})

onBeforeUnmount(() => {
  chart?.dispose()
})

watch([() => props.dimensions, () => props.comparisonData], () => {
  initChart()
}, { deep: true })
</script>
