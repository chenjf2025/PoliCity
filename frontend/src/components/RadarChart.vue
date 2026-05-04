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
      trigger: 'item',
      position: (point: any) => point,
      formatter: (params: any) => {
        // params.name 是 series 名称, value 是全量数组
        const values = Array.isArray(params.value) ? params.value : [params.value];
        const dimCount = values.length;

        // 通过 tooltip 相对于雷达图中心的位置来计算悬停的维度索引
        // 雷达图中心在容器 50%, 55% 位置
        const container = chartRef.value;
        if (!container) return '';

        const rect = container.getBoundingClientRect();
        const cx = rect.width * 0.5;
        const cy = rect.height * 0.55;
        const dx = (params.event?.offsetX ?? cx) - cx;
        const dy = (params.event?.offsetY ?? cy) - cy;

        // 计算角度，atan2给出数学标准角度（0°在右边，逆时针）
        // 转换为雷达图角度：0°在顶部，顺时针增加
        let angle = Math.atan2(dy, dx) * 180 / Math.PI;
        angle = (angle + 90 + 360) % 360; // 转换：0°在顶部，顺时针

        // 根据角度计算维度索引 (6个维度均匀分布，每个60度)
        // 每个维度覆盖前后30度的范围
        const dimIdx = Math.floor((angle + 30) / 60) % dimCount;

        const dim = props.dimensions[dimIdx];
        if (!dim) return '';
        const score = values[dimIdx] ?? 0;

        let html = `${params.marker} ${params.name || params.seriesName || ''}<br/><strong>${dim.name}</strong>: ${score}分<br/>(权重: ${(dim.weight * 100).toFixed(0)}%)`;
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
