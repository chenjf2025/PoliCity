import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const currentRegion = ref({
    code: 'default',
    name: '默认城市'
  })

  const reportYear = ref(2024)
  const reportMonth = ref<number | undefined>(undefined)

  const setRegion = (code: string, name: string) => {
    currentRegion.value = { code, name }
  }

  const setReportYear = (year: number) => {
    reportYear.value = year
  }

  const setReportMonth = (month: number | undefined) => {
    reportMonth.value = month
  }

  return {
    currentRegion,
    reportYear,
    reportMonth,
    setRegion,
    setReportYear,
    setReportMonth
  }
})
