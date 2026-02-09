# Reperio API Documentation

## Overview

The Reperio REST API provides endpoints for loading, analyzing, and visualizing Apache Nutch data structures.

Base URL: `http://localhost:8000`

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Endpoints

### Health Check

#### `GET /api/health`

Check API health and current graph status.

**Response:**
```json
{
  "status": "healthy",
  "graph_loaded": true,
  "num_nodes": 12345,
  "num_edges": 45678
}
```

### Graph Loading

#### `POST /api/graph/load`

Load Nutch data and build graph.

**Request Body:**
```json
{
  "path": "hdfs://namenode:9000/nutch/crawldb",
  "db_type": "crawldb",
  "storage": "hdfs",
  "max_records": 10000,
  "hdfs_config": {
    "namenode": "namenode.example.com",
    "port": 9000
  }
}
```

**Parameters:**
- `path` (string, required): Path to Nutch data (local or HDFS)
- `db_type` (string, required): One of: `crawldb`, `linkdb`, `hostdb`
- `storage` (string, optional): `local` or `hdfs` (default: `local`)
- `max_records` (int, optional): Maximum records to load
- `hdfs_config` (object, optional): HDFS configuration

**Response:**
```json
{
  "status": "success",
  "message": "Graph loaded successfully from crawldb",
  "data": {
    "db_type": "crawldb",
    "num_nodes": 12345,
    "num_edges": 45678
  }
}
```

### Graph Information

#### `GET /api/graph/summary`

Get graph statistics.

**Response:**
```json
{
  "num_nodes": 12345,
  "num_edges": 45678,
  "density": 0.0123,
  "is_directed": true,
  "num_strongly_connected_components": 150,
  "num_weakly_connected_components": 50
}
```

#### `GET /api/graph/data`

Get graph data for visualization.

**Query Parameters:**
- `max_nodes` (int, optional): Maximum nodes to include
- `format` (string, optional): `json` or `sigma` (default: `sigma`)

**Response (Sigma format):**
```json
{
  "nodes": [
    {
      "key": "http://example.com",
      "attributes": {
        "label": "example.com",
        "x": 123.45,
        "y": 678.90,
        "size": 5,
        "color": "#4CAF50",
        "status": "fetched",
        "score": 0.85
      }
    }
  ],
  "edges": [
    {
      "key": "e0",
      "source": "http://source.com",
      "target": "http://target.com",
      "attributes": {
        "anchor": "Link text"
      }
    }
  ]
}
```

### Graph Query

#### `GET /api/graph/nodes`

Get graph nodes with pagination.

**Query Parameters:**
- `limit` (int, optional): Maximum nodes to return (default: 100)
- `offset` (int, optional): Pagination offset (default: 0)
- `status` (string, optional): Filter by status

**Response:**
```json
{
  "nodes": [...],
  "total": 12345,
  "limit": 100,
  "offset": 0
}
```

#### `GET /api/graph/edges`

Get graph edges with pagination.

**Query Parameters:**
- `limit` (int, optional): Maximum edges to return (default: 100)
- `offset` (int, optional): Pagination offset (default: 0)

**Response:**
```json
{
  "edges": [...],
  "total": 45678,
  "limit": 100,
  "offset": 0
}
```

#### `GET /api/search`

Search for nodes by URL.

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (int, optional): Maximum results (default: 10)

**Response:**
```json
{
  "results": [
    {
      "id": "http://example.com/page",
      "attributes": {...}
    }
  ],
  "total": 5,
  "query": "example.com"
}
```

### Graph Analysis

#### `POST /api/graph/analyze`

Run graph analysis algorithms.

**Request Body:**
```json
{
  "analysis_type": "pagerank",
  "params": {
    "alpha": 0.85
  }
}
```

**Analysis Types:**
- `pagerank`: Calculate PageRank scores
  - Parameters: `alpha` (float, default: 0.85)
- `centrality`: Calculate degree centrality
  - Parameters: `type` (string, default: `in_degree`): `in_degree` or `out_degree`
- `components`: Find connected components
  - No parameters

**Response (PageRank):**
```json
{
  "type": "pagerank",
  "top_nodes": [
    ["http://important-page.com", 0.1234],
    ["http://another-page.com", 0.0987]
  ]
}
```

### Graph Operations

#### `POST /api/graph/filter`

Filter graph by criteria.

**Request Body:**
```json
{
  "filter_type": "status",
  "value": "fetched",
  "max_value": null
}
```

**Filter Types:**
- `status`: Filter by crawl status
- `domain`: Filter by domain regex pattern
- `score`: Filter by score range (use `value` as min, `max_value` as max)

**Response:**
```json
{
  "status": "success",
  "filtered_nodes": 5678,
  "filtered_edges": 12345
}
```

#### `POST /api/graph/export`

Export graph data.

**Request Body:**
```json
{
  "format": "json",
  "max_nodes": 10000,
  "include_clustering": false
}
```

**Parameters:**
- `format` (string, required): `json`, `sigma`, `gexf`, or `graphml`
- `max_nodes` (int, optional): Maximum nodes to export
- `include_clustering` (bool, optional): Include community detection (default: false)

**Response:**
Graph data in requested format.

### Host Analysis

#### `GET /api/hosts`

Get host-level statistics.

**Response:**
```json
{
  "total_hosts": 150,
  "top_hosts": [
    {
      "host": "example.com",
      "in_degree": 1000,
      "out_degree": 500,
      "total_degree": 1500
    }
  ],
  "host_graph_edges": 5000
}
```

### Configuration

#### `GET /api/config/hdfs`

Get current HDFS configuration.

**Response:**
```json
{
  "namenode": "localhost",
  "port": 9000,
  "hadoop_conf_dir": "/etc/hadoop/conf"
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found (e.g., no graph loaded)
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently, there is no rate limiting. This may be added in future versions.

## WebSocket Support

WebSocket support for real-time updates is planned for a future release.
