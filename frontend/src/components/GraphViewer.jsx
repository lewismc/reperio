import { useEffect, useRef, useState } from 'react'
import { SigmaContainer, useLoadGraph, useRegisterEvents, useSigma } from '@react-sigma/core'
import { useGraphStore } from '../store/graphStore'
import Graph from 'graphology'
import '@react-sigma/core/lib/react-sigma.min.css'
import './GraphViewer.css'

function GraphLoader() {
  const loadGraph = useLoadGraph()
  const { graphData } = useGraphStore()
  const sigma = useSigma()
  const registerEvents = useRegisterEvents()
  const [selectedNode, setSelectedNode] = useState(null)

  useEffect(() => {
    if (!graphData || !graphData.nodes) {
      console.log('No graph data available')
      return
    }

    console.log('Loading graph with', graphData.nodes.length, 'nodes and', graphData.edges.length, 'edges')

    const graph = new Graph()

    // Add nodes
    graphData.nodes.forEach((node) => {
      try {
        graph.addNode(node.key, {
          ...node.attributes,
          label: node.attributes.label || node.key,
          size: node.attributes.size || 5,
          color: node.attributes.color || '#646cff',
        })
      } catch (error) {
        console.error('Error adding node:', node.key, error)
      }
    })

    // Add edges
    graphData.edges.forEach((edge, index) => {
      try {
        if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
          graph.addEdge(edge.source, edge.target, {
            ...edge.attributes,
            size: 1,
            color: '#666',
          })
        }
      } catch (error) {
        console.error('Error adding edge:', edge, error)
      }
    })

    loadGraph(graph)

    // Setup event handlers
    registerEvents({
      clickNode: ({ node }) => {
        setSelectedNode(node)
        const nodeData = graph.getNodeAttributes(node)
        console.log('Node clicked:', node, nodeData)
      },
      clickStage: () => {
        setSelectedNode(null)
      },
    })

  }, [graphData, loadGraph, registerEvents])

  // Node info panel
  if (selectedNode) {
    const sigma = useSigma()
    const graph = sigma.getGraph()
    const nodeData = graph.getNodeAttributes(selectedNode)

    return (
      <div className="node-info-panel">
        <h3>Node Info</h3>
        <button className="close-btn" onClick={() => setSelectedNode(null)}>×</button>
        <div className="node-info-content">
          <p><strong>ID:</strong> {selectedNode}</p>
          <p><strong>Label:</strong> {nodeData.label}</p>
          {nodeData.status && <p><strong>Status:</strong> {nodeData.status}</p>}
          {nodeData.score !== undefined && <p><strong>Score:</strong> {nodeData.score.toFixed(4)}</p>}
          {nodeData.fetch_datetime && <p><strong>Fetched:</strong> {nodeData.fetch_datetime}</p>}
          <p><strong>In-degree:</strong> {graph.inDegree(selectedNode)}</p>
          <p><strong>Out-degree:</strong> {graph.outDegree(selectedNode)}</p>
        </div>
      </div>
    )
  }

  return null
}

function GraphViewer() {
  const { graphData } = useGraphStore()

  if (!graphData) {
    return (
      <div className="graph-viewer-empty">
        <p>No graph data available</p>
      </div>
    )
  }

  return (
    <div className="graph-viewer">
      <SigmaContainer
        style={{ height: '100%', width: '100%' }}
        settings={{
          renderEdgeLabels: false,
          defaultNodeColor: '#646cff',
          defaultEdgeColor: '#666',
          labelFont: 'Arial',
          labelSize: 12,
          labelWeight: 'normal',
          defaultNodeType: 'circle',
          minCameraRatio: 0.1,
          maxCameraRatio: 10,
        }}
      >
        <GraphLoader />
      </SigmaContainer>
    </div>
  )
}

export default GraphViewer
