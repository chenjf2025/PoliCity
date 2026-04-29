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
}

const props = defineProps<Props>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const COLORS = ['#fa8c16', '#52c41a', '#eb2f96', '#722ed1', '#13c2c2', '#faad14']

const initChart = () => {
  if (!chartRef.value) return

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
      text: '五维评价雷达图',
      left: 'center',
      top: 10
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const idx = params.dataIndex
        const dim = props.dimensions[idx]
        return `${params.marker} ${params.name}<br/>${dim.name}: ${params.value}分<br/>(权重: ${(dim.weight * 100).toFixed(0)}%)`
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

watch(() => [props.dimensions, props.comparisonData], () => {
  initChart()
}, { deep: true })
</script>
