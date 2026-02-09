import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { useGraphStore } from '../store/graphStore'
import './ControlPanel.css'

function ControlPanel({ onShowLoader, availableDatasets, setAvailableDatasets }) {
  const { graphData, metadata, setGraphData, setMetadata, setLoading, clearGraph } = useGraphStore()
  const [isOpen, setIsOpen] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [activeDataset, setActiveDataset] = useState(null)
  const [datasetsInfo, setDatasetsInfo] = useState(null)

  // Fetch available datasets on mount
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const data = await api.getDatasets()
        setDatasetsInfo(data.datasets)
        setActiveDataset(data.active_dataset)
        if (data.datasets && Object.keys(data.datasets).length > 0) {
          setAvailableDatasets(Object.keys(data.datasets))
        }
      } catch (err) {
        console.error('Failed to fetch datasets:', err)
      }
    }

    if (graphData) {
      fetchDatasets()
    }
  }, [graphData, setAvailableDatasets])

  const handleDatasetSwitch = async (datasetName) => {
    try {
      setLoading(true)
      
      // Activate the dataset on the backend
      const result = await api.activateDataset(datasetName)
      console.log('Dataset activated:', result)
      
      // Fetch the graph data for this dataset
      const graphData = await api.getGraphData(10000, 'sigma')
      setGraphData(graphData)
      setMetadata(result.metadata)
      setActiveDataset(datasetName)
      
      setLoading(false)
    } catch (err) {
      console.error('Failed to switch dataset:', err)
      alert('Failed to switch dataset: ' + err.message)
      setLoading(false)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    try {
      const results = await api.searchNodes(searchQuery, 10)
      setSearchResults(results)
    } catch (error) {
      console.error('Search failed:', error)
    }
  }

  const handleExport = async (format) => {
    try {
      const data = await api.exportGraph(format, null, false)
      
      // Download as JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `graph_export.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
      alert('Export failed: ' + error.message)
    }
  }

  const handleAnalyze = async (analysisType) => {
    try {
      const results = await api.analyzeGraph(analysisType)
      console.log('Analysis results:', results)
      
      // Display results
      const message = analysisType === 'pagerank' 
        ? `Top PageRank nodes:\n${results.top_nodes.map(([node, score]) => `${node}: ${score.toFixed(4)}`).join('\n')}`
        : analysisType === 'centrality'
        ? `Top centrality nodes:\n${results.top_nodes.map(([node, score]) => `${node}: ${score.toFixed(4)}`).join('\n')}`
        : `Connected Components:\nStrongly: ${results.num_strongly_connected}\nWeakly: ${results.num_weakly_connected}\nLargest: ${results.largest_component_size}`
      
      alert(message)
    } catch (error) {
      console.error('Analysis failed:', error)
      alert('Analysis failed: ' + error.message)
    }
  }

  return (
    <div className={`control-panel ${isOpen ? 'open' : 'closed'}`}>
      <button className="toggle-btn" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? '◀' : '▶'}
      </button>

      {isOpen && (
        <div className="control-panel-content">
          <h2>Controls</h2>

          {availableDatasets && availableDatasets.length > 1 && (
            <div className="control-section">
              <h3>Dataset</h3>
              <select 
                value={activeDataset || ''} 
                onChange={(e) => handleDatasetSwitch(e.target.value)}
                className="dataset-selector"
              >
                {availableDatasets.map(dataset => (
                  <option key={dataset} value={dataset}>
                    {dataset.toUpperCase()}
                    {datasetsInfo && datasetsInfo[dataset] && 
                      ` (${datasetsInfo[dataset].num_nodes?.toLocaleString() || 0} nodes)`
                    }
                  </option>
                ))}
              </select>
            </div>
          )}

          {metadata && (
            <div className="metadata-section">
              <h3>Graph Info</h3>
              <p><strong>Type:</strong> {metadata.db_type || activeDataset}</p>
              <p><strong>Nodes:</strong> {metadata.num_nodes?.toLocaleString()}</p>
              <p><strong>Edges:</strong> {metadata.num_edges?.toLocaleString()}</p>
            </div>
          )}

          <div className="control-section">
            <h3>Data</h3>
            <button onClick={onShowLoader}>Load New Data</button>
            <button onClick={() => clearGraph()}>Clear Graph</button>
          </div>

          <div className="control-section">
            <h3>Search</h3>
            <form onSubmit={handleSearch}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search URLs..."
              />
              <button type="submit">Search</button>
            </form>
            {searchResults && (
              <div className="search-results">
                <p>{searchResults.total} results found</p>
                {searchResults.results.map((result, idx) => (
                  <div key={idx} className="search-result-item">
                    <small>{result.id}</small>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="control-section">
            <h3>Analysis</h3>
            <button onClick={() => handleAnalyze('pagerank')}>PageRank</button>
            <button onClick={() => handleAnalyze('centrality')}>Centrality</button>
            <button onClick={() => handleAnalyze('components')}>Components</button>
          </div>

          <div className="control-section">
            <h3>Export</h3>
            <button onClick={() => handleExport('json')}>Export JSON</button>
            <button onClick={() => handleExport('sigma')}>Export Sigma</button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ControlPanel
