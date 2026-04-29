import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API请求失败:', error.response?.data?.detail || error.message)
    return Promise.reject(error)
  }
)

// 指标管理API
export const indicatorAPI = {
  list: (params?: { dimension?: string; status?: number }) =>
    apiClient.get('/indicators', { params }),

  getDimensions: () =>
    apiClient.get('/indicators/dimensions'),

  getByCode: (code: string) =>
    apiClient.get(`/indicators/${code}`),

  create: (data: any) =>
    apiClient.post('/indicators', data),

  update: (code: string, data: any) =>
    apiClient.put(`/indicators/${code}`, data),

  delete: (code: string) =>
    apiClient.delete(`/indicators/${code}`)
}

// 数据采集API
export const dataAPI = {
  importExcel: (file: FormData, reportYear: number) => {
    return apiClient.post(`/data/raw/import?report_year=${reportYear}`, file)
  },

  createRaw: (data: any) =>
    apiClient.post('/data/raw', data),

  listRaw: (params?: any) =>
    apiClient.get('/data/raw', { params }),

  normalize: (reportYear: number, reportMonth?: number) =>
    apiClient.post('/data/normalize', { report_year: reportYear, report_month: reportMonth }),

  getStandardScores: (regionCode: string, reportYear: number, reportMonth?: number) =>
    apiClient.get('/data/standard-score', { params: { region_code: regionCode, report_year: reportYear, report_month: reportMonth } })
}

// 评价引擎API
export const evaluationAPI = {
  getRadar: (regionCode: string, reportYear: number, reportMonth?: number) =>
    apiClient.get('/evaluation/radar', { params: { region_code: regionCode, report_year: reportYear, report_month: reportMonth } }),

  getTotal: (regionCode: string, reportYear: number, reportMonth?: number) =>
    apiClient.get('/evaluation/total', { params: { region_code: regionCode, report_year: reportYear, report_month: reportMonth } }),

  getTrend: (regionCode: string, years?: number) =>
    apiClient.get('/evaluation/trend', { params: { region_code: regionCode, years } }),

  getShortboard: (regionCode: string, reportYear: number, benchmarkRegionCode?: string, threshold?: number) =>
    apiClient.get('/evaluation/shortboard', { params: { region_code: regionCode, report_year: reportYear, benchmark_region_code: benchmarkRegionCode, threshold } }),

  getDimensionDetail: (dimension: string, regionCode: string, reportYear: number) =>
    apiClient.get(`/evaluation/dimension/${dimension}`, { params: { region_code: regionCode, report_year: reportYear } })
}

// 政策仿真API
export const simulationAPI = {
  whatIf: (params: {
    region_code: string
    region_name: string
    report_year: number
    simulation_params: Array<{ indicator_code: string; simulated_value: number }>
    user_id?: string
    simulation_name?: string
  }) => apiClient.post('/simulation/what-if', params),

  getHistory: (params?: { region_code?: string; user_id?: string; limit?: number }) =>
    apiClient.get('/simulation/history', { params }),

  getDetail: (simulationId: string) =>
    apiClient.get(`/simulation/${simulationId}`),

  agentAnalyze: (params: {
    region_code: string
    region_name: string
    report_year: number
    policy_changes: Array<{ indicator_code: string; change_percent: number }>
  }) => apiClient.post('/simulation/agent-analyze', params),

  agentAnalyzeStream: (params: {
    region_code: string
    region_name: string
    report_year: number
    policy_changes: Array<{ indicator_code: string; change_percent: number }>
  }) => {
    const searchParams = new URLSearchParams({
      query: JSON.stringify(params),
      user_id: 'anonymous'
    })
    return fetch(`/api/v1/simulation/agent-analyze-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    })
  },

  getFullAnalysis: (regionCode: string, reportYear: number) =>
    apiClient.get('/simulation/agent/full-analysis', { params: { region_code: regionCode, report_year: reportYear } })
}

// 对标分析API
export const benchmarkAPI = {
  listCities: (cityLevel?: string) =>
    apiClient.get('/benchmark/cities', { params: { city_level: cityLevel } }),

  addCity: (data: any) =>
    apiClient.post('/benchmark/cities', data),

  compare: (params: {
    region_code: string
    region_name: string
    benchmark_city_codes: string[]
    report_year: number
  }) => apiClient.post('/benchmark/compare', params)
}

// Dify AI API
export const difyAPI = {
  chat: (params: { query: string; user_id?: string; conversation_id?: string }) =>
    apiClient.post('/dify/chat', params),

  chatStream: (params: { query: string; user_id?: string; conversation_id?: string }) => {
    return new EventSource(`/api/v1/dify/chat/stream?${new URLSearchParams({
      query: params.query,
      user_id: params.user_id || 'anonymous',
      conversation_id: params.conversation_id || ''
    })}`)
  },

  getConversations: (userId?: string, limit?: number) =>
    apiClient.get('/dify/conversations', { params: { user_id: userId, limit } }),

  getMessages: (conversationId: string, userId?: string) =>
    apiClient.get('/dify/messages', { params: { conversation_id: conversationId, user_id: userId } })
}

// 流式调用Dify聊天API (返回fetch流对象)
export const difyChatStream = (params: { query: string; user_id?: string; conversation_id?: string }) => {
  const searchParams = new URLSearchParams({
    query: params.query,
    user_id: params.user_id || 'anonymous'
  })
  if (params.conversation_id) {
    searchParams.set('conversation_id', params.conversation_id)
  }

  return fetch(`/api/v1/dify/chat/stream?${searchParams}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(params)
  })
}

export default apiClient
