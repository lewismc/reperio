import { useState } from 'react'
import { api } from '../api/client'
import { useGraphStore } from '../store/graphStore'
import './DataLoader.css'

function DataLoader({ onClose }) {
  const { setGraphData, setMetadata, setLoading, setError } = useGraphStore()
  
  const [path, setPath] = useState('')
  const [dbType, setDbType] = useState('crawldb')
  const [storage, setStorage] = useState('local')
  const [maxRecords, setMaxRecords] = useState('')
  const [hdfsNamenode, setHdfsNamenode] = useState('localhost')
  const [hdfsPort, setHdfsPort] = useState('9000')
  const [loading, setLocalLoading] = useState(false)
  const [error, setLocalError] = useState(null)

  const handleLoad = async (e) => {
    e.preventDefault()
    setLocalLoading(true)
    setLocalError(null)
    setLoading(true)

    try {
      // Load graph
      const hdfsConfig = storage === 'hdfs' ? {
        namenode: hdfsNamenode,
        port: parseInt(hdfsPort),
      } : null

      const loadResult = await api.loadGraph(
        path,
        dbType,
        storage,
        maxRecords ? parseInt(maxRecords) : null,
        hdfsConfig
      )

      console.log('Load result:', loadResult)

      // Get graph data for visualization
      const graphData = await api.getGraphData(10000, 'sigma')
      console.log('Graph data:', graphData)

      setGraphData(graphData)
      setMetadata(loadResult.data)
      
      setLocalLoading(false)
      setLoading(false)
      
      if (onClose) {
        onClose()
      }
    } catch (err) {
      console.error('Error loading graph:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load graph'
      setLocalError(errorMessage)
      setError(errorMessage)
      setLocalLoading(false)
      setLoading(false)
    }
  }

  const handleTest = async () => {
    setLocalLoading(true)
    setLocalError(null)

    try {
      const health = await api.healthCheck()
      alert(`API is healthy!\n\nGraph loaded: ${health.graph_loaded}\nNodes: ${health.num_nodes}\nEdges: ${health.num_edges}`)
      setLocalError(null)
    } catch (err) {
      setLocalError(`API connection failed: ${err.message}`)
    } finally {
      setLocalLoading(false)
    }
  }

  return (
    <div className="data-loader">
      <div className="data-loader-content">
        <h2>Load Nutch Data</h2>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <form onSubmit={handleLoad}>
          <div className="form-group">
            <label htmlFor="dbType">Database Type:</label>
            <select
              id="dbType"
              value={dbType}
              onChange={(e) => setDbType(e.target.value)}
              required
            >
              <option value="crawldb">CrawlDB</option>
              <option value="linkdb">LinkDB</option>
              <option value="hostdb">HostDB</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="storage">Storage:</label>
            <select
              id="storage"
              value={storage}
              onChange={(e) => setStorage(e.target.value)}
              required
            >
              <option value="local">Local Filesystem</option>
              <option value="hdfs">HDFS</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="path">Path:</label>
            <input
              id="path"
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder={storage === 'hdfs' ? 'hdfs://namenode:9000/path/to/data' : '/path/to/crawldb'}
              required
            />
            <small>
              {storage === 'hdfs' 
                ? 'HDFS path (e.g., hdfs://namenode:9000/nutch/crawldb)' 
                : 'Local filesystem path'}
            </small>
          </div>

          {storage === 'hdfs' && (
            <>
              <div className="form-group">
                <label htmlFor="namenode">HDFS Namenode:</label>
                <input
                  id="namenode"
                  type="text"
                  value={hdfsNamenode}
                  onChange={(e) => setHdfsNamenode(e.target.value)}
                  placeholder="localhost"
                />
              </div>

              <div className="form-group">
                <label htmlFor="port">HDFS Port:</label>
                <input
                  id="port"
                  type="number"
                  value={hdfsPort}
                  onChange={(e) => setHdfsPort(e.target.value)}
                  placeholder="9000"
                />
              </div>
            </>
          )}

          <div className="form-group">
            <label htmlFor="maxRecords">Max Records (optional):</label>
            <input
              id="maxRecords"
              type="number"
              value={maxRecords}
              onChange={(e) => setMaxRecords(e.target.value)}
              placeholder="Leave empty for all records"
            />
            <small>Limit the number of records to load (useful for testing)</small>
          </div>

          <div className="form-actions">
            <button type="button" onClick={handleTest} disabled={loading}>
              Test Connection
            </button>
            <button type="submit" disabled={loading}>
              {loading ? 'Loading...' : 'Load Data'}
            </button>
            {onClose && (
              <button type="button" onClick={onClose} disabled={loading}>
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}

export default DataLoader
