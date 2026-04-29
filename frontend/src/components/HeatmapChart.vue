<template>
  <div ref="chartRef" class="heatmap-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

interface RegionData {
  name: string
  value: number
  rank?: number
}

interface Props {
  data: RegionData[]
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '区域发展热力图'
})

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)

  // 模拟的地理数据（实际项目需要GeoJSON）
  const geoCoordMap: Record<string, [number, number]> = {
    '城区': [119.5, 32.5],
    '郊区': [119.6, 32.6],
    '开发区': [119.7, 32.4],
    '高新区': [119.4, 32.7],
    '周边县': [119.8, 32.3]
  }

  const convertedData = props.data.map(d => {
    const coord = geoCoordMap[d.name] || [119.5 + Math.random() * 0.5, 32.5 + Math.random() * 0.4]
    return {
      name: d.name,
      value: [...coord, d.value]
    }
  })

  const option = {
    title: {
      text: props.title,
      left: 'center',
      top: 10
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.name}<br/>得分: ${params.value[2] || 0}`
      }
    },
    visualMap: {
      min: 0,
      max: 100,
      left: 'left',
      top: 'bottom',
      text: ['高', '低'],
      calculable: true,
      inRange: {
        color: ['#50a3ba', '#eac736', '#d94e5d']
      }
    },
    geo: {
      map: 'china',
      roam: false,
      label: {
        show: false
      },
      itemStyle: {
        areaColor: '#e0e0e0',
        borderColor: '#fff'
      }
    },
    series: [
      {
        name: '发展得分',
        type: 'scatter',
        coordinateSystem: 'geo',
        data: convertedData,
        symbolSize: (val: number[]) => Math.max(20, val[2] / 3),
        label: {
          show: true,
          formatter: (params: any) => params.name,
          position: 'right'
        },
        itemStyle: {
          color: '#5470c6'
        },
        emphasis: {
          label: {
            show: true
          }
        }
      }
    ]
  }

  // 尝试注册简化的地图
  try {
    echarts.registerMap('china', {
      type: 'FeatureCollection',
      features: []
    })
  } catch (e) {
    // 忽略地图注册错误
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

watch(() => props.data, () => {
  initChart()
}, { deep: true })
</script>
