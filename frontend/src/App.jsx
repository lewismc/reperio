import { useState, useEffect } from 'react'
import './App.css'
import DataLoader from './components/DataLoader'
import GraphViewer from './components/GraphViewer'
import ControlPanel from './components/ControlPanel'
import { useGraphStore } from './store/graphStore'
import { api } from './api/client'

function App() {
  const { graphData, isLoading, setGraphData, setLoading, setError } = useGraphStore()
  const [showLoader, setShowLoader] = useState(false)
  const [availableDatasets, setAvailableDatasets] = useState([])
  const [checkingPreloaded, setCheckingPreloaded] = useState(true)

  // Check if data is already loaded by CLI on mount
  useEffect(() => {
    const checkPreloadedData = async () => {
      try {
        const status = await api.getStatus()
        
        if (status.graph_loaded && status.loaded_datasets && status.loaded_datasets.length > 0) {
          // Data was already loaded by CLI!
          console.log('Data pre-loaded by CLI:', status.loaded_datasets)
          setAvailableDatasets(status.loaded_datasets)
          
          // Load the active dataset's graph data
          setLoading(true)
          const graphData = await api.getGraphData(10000, 'sigma')
          setGraphData(graphData)
          setLoading(false)
          setCheckingPreloaded(false)
          setShowLoader(false)
        } else {
          // No data loaded - show the loader form
          console.log('No data pre-loaded, showing loader form')
          setCheckingPreloaded(false)
          setShowLoader(true)
        }
      } catch (err) {
        console.error('Error checking pre-loaded data:', err)
        setError(err.message)
        setCheckingPreloaded(false)
        setShowLoader(true)
      }
    }

    checkPreloadedData()
  }, [setGraphData, setLoading, setError])

  if (checkingPreloaded) {
    return (
      <div className="app">
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Checking for pre-loaded data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Reperio</h1>
        <p>Apache Nutch Data Visualization</p>
        {availableDatasets.length > 0 && (
          <div className="loaded-datasets-info">
            <span>Loaded: {availableDatasets.map(d => d.toUpperCase()).join(', ')}</span>
          </div>
        )}
      </header>

      <div className="app-content">
        {showLoader && !graphData ? (
          <DataLoader onClose={() => setShowLoader(false)} />
        ) : (
          <>
            <ControlPanel 
              onShowLoader={() => setShowLoader(true)} 
              availableDatasets={availableDatasets}
              setAvailableDatasets={setAvailableDatasets}
            />
            <div className="graph-container">
              {isLoading && (
                <div className="loading-overlay">
                  <div className="spinner"></div>
                  <p>Loading graph data...</p>
                </div>
              )}
              {graphData && <GraphViewer />}
              {!graphData && !isLoading && (
                <div className="empty-state">
                  <h2>No Data Loaded</h2>
                  <p>Data can be pre-loaded via CLI or loaded here</p>
                  <button onClick={() => setShowLoader(true)}>Load Data</button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default App
