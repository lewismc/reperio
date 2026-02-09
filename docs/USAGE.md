# Usage Guide

Comprehensive guide for using Reperio to visualize Apache Nutch data.

## Table of Contents

- [Getting Started](#getting-started)
- [CLI Usage](#cli-usage)
- [Web Interface](#web-interface)
- [API Usage](#api-usage)
- [Data Sources](#data-sources)
- [Graph Analysis](#graph-analysis)
- [Export Options](#export-options)

## Getting Started

### Understanding Nutch Data Structures

**CrawlDB**: Contains information about each URL crawled:
- URL
- Fetch status (fetched, unfetched, redirect, gone, etc.)
- Fetch time
- Score
- Retry count
- Metadata

**LinkDB**: Contains the link graph:
- Target URL
- List of source URLs (inlinks)
- Anchor text for each link

**HostDB**: Contains host-level aggregations:
- Hostname
- Homepage URL
- Statistics (fetched count, errors, response times, etc.)

## CLI Usage

### View Statistics

```bash
# CrawlDB statistics
poetry run reperio stats /path/to/crawldb --type crawldb

# LinkDB statistics
poetry run reperio stats /path/to/linkdb --type linkdb

# Limit records for faster analysis
poetry run reperio stats /path/to/crawldb --type crawldb --max-records 10000

# HDFS path
poetry run reperio stats hdfs://namenode:9000/nutch/crawldb --type crawldb \
  --namenode namenode.example.com --port 9000
```

**Note**: All examples use `poetry run` for Poetry 2.0+ compatibility. If you're in an activated virtual environment, you can omit `poetry run`.

### Load and Export Data

```bash
# Export CrawlDB as JSON graph
poetry run reperio export /path/to/crawldb output.json \
  --type crawldb --format json

# Export LinkDB as GEXF (for Gephi)
poetry run reperio export /path/to/linkdb output.gexf \
  --type linkdb --format gexf

# Export with record limit
poetry run reperio export /path/to/crawldb output.json \
  --type crawldb --format json --max-records 5000

# Export Sigma.js format for web visualization
poetry run reperio export /path/to/linkdb output.json \
  --type linkdb --format sigma
```

### Start API Server

```bash
# Default (localhost:8000)
poetry run reperio serve

# Custom host and port
poetry run reperio serve --host 0.0.0.0 --port 9000

# Development mode with auto-reload
poetry run reperio serve --reload
```

### Launch Web UI

```bash
# Start server and open browser
poetry run reperio web

# Custom port
poetry run reperio web --port 9000

# Don't open browser automatically
poetry run reperio web --no-open
```

## Web Interface

### Loading Data

1. Click "Load Data" button
2. Select database type (CrawlDB, LinkDB, or HostDB)
3. Choose storage type (Local or HDFS)
4. Enter path to data
5. (Optional) Configure HDFS settings
6. (Optional) Set max records for testing
7. Click "Test Connection" to verify
8. Click "Load Data" to load

### Navigating the Graph

**Mouse controls:**
- **Left click + drag**: Pan the graph
- **Scroll wheel**: Zoom in/out
- **Click node**: Show node details
- **Click background**: Deselect node

**Keyboard shortcuts:**
- `Space`: Reset camera
- `+/-`: Zoom in/out
- `Escape`: Close panels

### Searching

1. Enter URL pattern in search box
2. Press Enter or click "Search"
3. Results appear in sidebar
4. Click result to highlight in graph

### Filtering

Filter nodes by:
- **Status**: Show only fetched/unfetched/error URLs
- **Domain**: Show URLs matching regex pattern
- **Score**: Show URLs in score range

### Analysis Tools

#### PageRank
Identifies most important pages based on link structure.

1. Click "PageRank" button
2. View top-ranked pages
3. High PageRank = many inlinks from important pages

#### Centrality
Measures node importance by degree (number of connections).

1. Click "Centrality" button
2. View nodes with most inlinks/outlinks
3. Useful for finding hubs and authorities

#### Connected Components
Finds isolated subgraphs.

1. Click "Components" button
2. View number of components
3. Identifies disconnected parts of the graph

### Export

Export graph data for external analysis:

1. Click export format:
   - **JSON**: Generic graph format
   - **Sigma**: Sigma.js format with positions
   - **GEXF**: For Gephi visualization software
   - **GraphML**: For network analysis tools

2. File downloads automatically

## API Usage

### Python Example

```python
import requests

# API base URL
BASE_URL = "http://localhost:8000"

# Load graph from HDFS
response = requests.post(f"{BASE_URL}/api/graph/load", json={
    "path": "hdfs://namenode:9000/nutch/crawldb",
    "db_type": "crawldb",
    "storage": "hdfs",
    "max_records": 10000,
    "hdfs_config": {
        "namenode": "namenode.example.com",
        "port": 9000
    }
})

# Check response
if response.status_code == 200:
    data = response.json()
    print(f"Loaded {data['data']['num_nodes']} nodes")

# Get graph summary
summary = requests.get(f"{BASE_URL}/api/graph/summary").json()
print(f"Graph density: {summary['density']:.4f}")

# Run PageRank analysis
analysis = requests.post(f"{BASE_URL}/api/graph/analyze", json={
    "analysis_type": "pagerank",
    "params": {"alpha": 0.85}
}).json()

# Print top pages
print("Top pages by PageRank:")
for url, score in analysis["top_nodes"][:10]:
    print(f"  {url}: {score:.4f}")

# Search for URLs
results = requests.get(f"{BASE_URL}/api/search", params={
    "q": "example.com",
    "limit": 20
}).json()

print(f"Found {results['total']} matching URLs")

# Export graph
export = requests.post(f"{BASE_URL}/api/graph/export", json={
    "format": "json",
    "max_nodes": 5000,
    "include_clustering": True
}).json()

# Save to file
import json
with open("graph_export.json", "w") as f:
    json.dump(export, f, indent=2)
```

### JavaScript Example

```javascript
// API client
const API_BASE = 'http://localhost:8000';

// Load graph
async function loadGraph() {
  const response = await fetch(`${API_BASE}/api/graph/load`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: '/path/to/crawldb',
      db_type: 'crawldb',
      storage: 'local',
      max_records: 10000
    })
  });
  
  const data = await response.json();
  console.log(`Loaded ${data.data.num_nodes} nodes`);
}

// Get visualization data
async function getGraphData() {
  const response = await fetch(
    `${API_BASE}/api/graph/data?format=sigma&max_nodes=5000`
  );
  
  const graphData = await response.json();
  return graphData;
}

// Search nodes
async function searchNodes(query) {
  const response = await fetch(
    `${API_BASE}/api/search?q=${encodeURIComponent(query)}&limit=10`
  );
  
  const results = await response.json();
  return results.results;
}

// Run analysis
async function runPageRank() {
  const response = await fetch(`${API_BASE}/api/graph/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      analysis_type: 'pagerank',
      params: { alpha: 0.85 }
    })
  });
  
  const analysis = await response.json();
  console.log('Top nodes:', analysis.top_nodes);
}
```

## Data Sources

### Local Filesystem

Works with any local SequenceFiles:

```bash
# Direct path
poetry run reperio stats /var/nutch/crawldb/current --type crawldb

# With file:// scheme
poetry run reperio stats file:///var/nutch/crawldb/current --type crawldb
```

### HDFS

Requires HDFS access and optional pyarrow:

```bash
# Install HDFS support
poetry install --extras hdfs

# Use HDFS path
poetry run reperio stats hdfs://namenode:9000/nutch/crawldb --type crawldb

# Configure namenode
poetry run reperio stats hdfs://namenode:9000/nutch/crawldb --type crawldb \
  --namenode namenode.example.com --port 9000

# Use environment variables
export HDFS_NAMENODE=namenode.example.com
export HDFS_PORT=9000
poetry run reperio stats hdfs:///nutch/crawldb --type crawldb
```

## Graph Analysis

### PageRank

Measures page importance based on link structure.

**Use cases:**
- Find most authoritative pages
- Identify link hubs
- Prioritize crawling

**Interpretation:**
- Higher score = more important
- Scores sum to 1.0 across all nodes
- Typical range: 0.0001 to 0.1

### Degree Centrality

Measures importance by number of connections.

**In-degree centrality**: Number of inbound links
- High in-degree = popular page
- Useful for finding authorities

**Out-degree centrality**: Number of outbound links
- High out-degree = hub page
- Useful for finding link farms

### Connected Components

Finds isolated subgraphs.

**Strongly connected**: Every node reaches every other node
**Weakly connected**: Ignoring edge direction

**Use cases:**
- Identify disconnected site sections
- Find isolated content clusters
- Detect link islands

### Host-level Analysis

Aggregates statistics by hostname.

**Metrics:**
- Total URLs per host
- Fetch success rate
- Error counts (404, DNS, connection)
- Average response time

**Use cases:**
- Identify problematic hosts
- Prioritize by host size
- Monitor host health

## Export Options

### JSON Format

Generic graph format:

```json
{
  "nodes": [
    {
      "id": "http://example.com",
      "label": "example.com",
      "status": "fetched",
      "score": 0.85
    }
  ],
  "edges": [
    {
      "source": "http://source.com",
      "target": "http://target.com",
      "anchor": "Link text"
    }
  ]
}
```

### Sigma.js Format

Includes positions for visualization:

```json
{
  "nodes": [
    {
      "key": "http://example.com",
      "attributes": {
        "x": 123.45,
        "y": 678.90,
        "size": 5,
        "color": "#4CAF50"
      }
    }
  ]
}
```

### GEXF Format

For Gephi visualization software.

**Import in Gephi:**
1. File → Open
2. Select .gexf file
3. Choose layout (ForceAtlas2 recommended)
4. Customize appearance

### GraphML Format

For network analysis tools (NetworkX, igraph, etc.).

**Load in Python:**
```python
import networkx as nx
G = nx.read_graphml("graph.graphml")
```

## Tips and Best Practices

### Performance

1. **Start small**: Use `--max-records` for testing
2. **Sample large graphs**: Load subset for exploration
3. **Use filtering**: Reduce visual clutter
4. **Export for analysis**: Use external tools for heavy computation

### Visualization

1. **Color by status**: Easily identify fetched/unfetched URLs
2. **Size by degree**: Highlight important nodes
3. **Filter noise**: Hide low-score or error URLs
4. **Use search**: Find specific domains quickly

### Analysis

1. **Combine metrics**: Use PageRank + centrality
2. **Compare components**: Analyze each cluster separately
3. **Track over time**: Compare successive crawls
4. **Host-level first**: Start with aggregated view

### HDFS

1. **Test connectivity**: Use `hdfs dfs -ls` first
2. **Check Kerberos**: Run `klist` to verify ticket
3. **Use namenode HA**: Configure failover
4. **Cache locally**: Export for repeated analysis
