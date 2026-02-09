import { create } from 'zustand'

export const useGraphStore = create((set) => ({
  graphData: null,
  metadata: null,
  isLoading: false,
  error: null,
  filters: {
    status: null,
    domain: null,
    minScore: null,
  },

  setGraphData: (data) => set({ graphData: data, error: null }),
  setMetadata: (metadata) => set({ metadata }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  
  setFilters: (filters) => set({ filters }),
  
  clearGraph: () => set({ 
    graphData: null, 
    metadata: null, 
    error: null,
    filters: { status: null, domain: null, minScore: null }
  }),
}))
