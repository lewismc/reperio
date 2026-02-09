import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// API methods
export const api = {
  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/api/health')
    return response.data
  },

  // Load graph data
  loadGraph: async (path, dbType, storage = 'local', maxRecords = null, hdfsConfig = null) => {
    const response = await apiClient.post('/api/graph/load', {
      path,
      db_type: dbType,
      storage,
      max_records: maxRecords,
      hdfs_config: hdfsConfig,
    })
    return response.data
  },

  // Get graph summary
  getGraphSummary: async () => {
    const response = await apiClient.get('/api/graph/summary')
    return response.data
  },

  // Get graph data for visualization
  getGraphData: async (maxNodes = null, format = 'sigma') => {
    const response = await apiClient.get('/api/graph/data', {
      params: { max_nodes: maxNodes, format },
    })
    return response.data
  },

  // Get nodes with pagination
  getNodes: async (limit = 100, offset = 0, status = null) => {
    const response = await apiClient.get('/api/graph/nodes', {
      params: { limit, offset, status },
    })
    return response.data
  },

  // Get edges with pagination
  getEdges: async (limit = 100, offset = 0) => {
    const response = await apiClient.get('/api/graph/edges', {
      params: { limit, offset },
    })
    return response.data
  },

  // Filter graph
  filterGraph: async (filterType, value, maxValue = null) => {
    const response = await apiClient.post('/api/graph/filter', {
      filter_type: filterType,
      value,
      max_value: maxValue,
    })
    return response.data
  },

  // Export graph
  exportGraph: async (format, maxNodes = null, includeClustering = false) => {
    const response = await apiClient.post('/api/graph/export', {
      format,
      max_nodes: maxNodes,
      include_clustering: includeClustering,
    })
    return response.data
  },

  // Analyze graph
  analyzeGraph: async (analysisType, params = null) => {
    const response = await apiClient.post('/api/graph/analyze', {
      analysis_type: analysisType,
      params,
    })
    return response.data
  },

  // Search nodes
  searchNodes: async (query, limit = 10) => {
    const response = await apiClient.get('/api/search', {
      params: { q: query, limit },
    })
    return response.data
  },

  // Get host statistics
  getHostStatistics: async () => {
    const response = await apiClient.get('/api/hosts')
    return response.data
  },

  // Get HDFS configuration
  getHDFSConfig: async () => {
    const response = await apiClient.get('/api/config/hdfs')
    return response.data
  },

  // Get loaded datasets
  getDatasets: async () => {
    const response = await apiClient.get('/api/datasets')
    return response.data
  },

  // Activate a specific dataset
  activateDataset: async (datasetName) => {
    const response = await apiClient.post(`/api/datasets/${datasetName}/activate`)
    return response.data
  },
  
  // Get API status
  getStatus: async () => {
    const response = await apiClient.get('/api/status')
    return response.data
  },
}

export default api
