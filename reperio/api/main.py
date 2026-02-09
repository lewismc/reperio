"""FastAPI main application."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from reperio.api.models import (
    AnalysisRequest,
    ExportRequest,
    FilterRequest,
    GraphDataResponse,
    GraphSummary,
    LoadGraphRequest,
    StatusResponse,
)
from reperio.config import get_config
from reperio.graph.graph_builder import GraphBuilder
from reperio.graph.graph_exporter import GraphExporter
from reperio.parsers.crawldb_parser import CrawlDBParser
from reperio.parsers.hostdb_parser import HostDBParser
from reperio.parsers.linkdb_parser import LinkDBParser
from reperio.readers.filesystem import FileSystemManager
from reperio.readers.sequencefile_reader import NutchSequenceFileReader

# Initialize FastAPI app
app = FastAPI(
    title="Reperio API",
    description="REST API for Apache Nutch data visualization",
    version="0.1.0",
)

# Get configuration
config = get_config()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use proper state management/database)
# Support multiple loaded datasets
loaded_datasets: Dict[str, Dict[str, Any]] = {}
active_dataset: Optional[str] = None


def set_graph(graph: nx.DiGraph, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Set the current graph (called from CLI on startup).
    
    Args:
        graph: NetworkX graph to serve
        metadata: Optional metadata about the graph
    """
    global active_dataset
    
    # Extract dataset name from metadata or use default
    dataset_name = metadata.get("db_type", "default") if metadata else "default"
    
    loaded_datasets[dataset_name] = {
        "graph": graph,
        "builder": None,  # Will be set if needed
        "metadata": metadata or {
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges(),
            "directed": graph.is_directed(),
        }
    }
    
    # Set as active if it's the first/only dataset
    if active_dataset is None:
        active_dataset = dataset_name


def add_dataset(dataset_name: str, graph: nx.DiGraph, builder: Optional[GraphBuilder] = None, 
                metadata: Optional[Dict[str, Any]] = None) -> None:
    """Add a dataset to the loaded datasets.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'crawldb', 'linkdb')
        graph: NetworkX graph
        builder: Optional graph builder instance
        metadata: Optional metadata about the dataset
    """
    global active_dataset
    
    loaded_datasets[dataset_name] = {
        "graph": graph,
        "builder": builder,
        "metadata": metadata or {
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges(),
            "directed": graph.is_directed(),
            "db_type": dataset_name,
        }
    }
    
    # Set as active if it's the first dataset
    if active_dataset is None:
        active_dataset = dataset_name


def get_active_graph() -> Optional[nx.DiGraph]:
    """Get the currently active graph."""
    if active_dataset and active_dataset in loaded_datasets:
        return loaded_datasets[active_dataset]["graph"]
    return None


def get_active_builder() -> Optional[GraphBuilder]:
    """Get the currently active graph builder."""
    if active_dataset and active_dataset in loaded_datasets:
        return loaded_datasets[active_dataset]["builder"]
    return None


def get_active_metadata() -> Dict[str, Any]:
    """Get the currently active metadata."""
    if active_dataset and active_dataset in loaded_datasets:
        return loaded_datasets[active_dataset]["metadata"]
    return {}


@app.get("/api/status")
async def api_status():
    """API status endpoint (root is served by frontend)."""
    return {
        "message": "Reperio API",
        "version": "0.1.0",
        "docs": "/docs",
        "graph_loaded": len(loaded_datasets) > 0,
        "loaded_datasets": list(loaded_datasets.keys()),
        "active_dataset": active_dataset,
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    current_graph = get_active_graph()
    return {
        "status": "healthy",
        "graph_loaded": current_graph is not None,
        "loaded_datasets": list(loaded_datasets.keys()),
        "active_dataset": active_dataset,
        "num_nodes": current_graph.number_of_nodes() if current_graph else 0,
        "num_edges": current_graph.number_of_edges() if current_graph else 0,
    }


@app.get("/api/datasets")
async def get_datasets():
    """Get list of loaded datasets.
    
    Returns:
        Dict: List of loaded datasets with metadata
    """
    datasets_info = {}
    for name, data in loaded_datasets.items():
        datasets_info[name] = {
            "name": name,
            "active": name == active_dataset,
            "num_nodes": data["graph"].number_of_nodes(),
            "num_edges": data["graph"].number_of_edges(),
            "metadata": data["metadata"],
        }
    
    return {
        "datasets": datasets_info,
        "active_dataset": active_dataset,
        "total_loaded": len(loaded_datasets),
    }


@app.post("/api/datasets/{dataset_name}/activate")
async def activate_dataset_endpoint(dataset_name: str):
    """Activate a specific dataset.
    
    Args:
        dataset_name: Name of the dataset to activate
        
    Returns:
        Dict: Activation status
    """
    global active_dataset
    
    if dataset_name not in loaded_datasets:
        raise HTTPException(
            status_code=404, 
            detail=f"Dataset '{dataset_name}' not found. Available: {list(loaded_datasets.keys())}"
        )
    
    active_dataset = dataset_name
    graph = loaded_datasets[dataset_name]["graph"]
    
    return {
        "status": "success",
        "active_dataset": active_dataset,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "metadata": loaded_datasets[dataset_name]["metadata"],
    }


@app.post("/api/graph/load", response_model=StatusResponse)
async def load_graph(request: LoadGraphRequest):
    """Load Nutch data and build graph.

    Args:
        request: Load graph request with path and config

    Returns:
        StatusResponse: Loading status
    """
    global active_dataset

    try:
        # Create filesystem manager
        hdfs_config = request.hdfs_config or {}
        fs_manager = FileSystemManager.create(
            path=request.path,
            namenode=hdfs_config.get("namenode", config.hdfs_namenode),
            port=hdfs_config.get("port", config.hdfs_port),
            hadoop_conf_dir=hdfs_config.get("hadoop_conf_dir", config.hadoop_conf_dir),
        )

        # Create reader
        reader = NutchSequenceFileReader(
            file_path=request.path, db_type=request.db_type, fs_manager=fs_manager
        )

        # Create graph builder
        builder = GraphBuilder()

        # Parse and build graph based on db_type
        if request.db_type.lower() == "crawldb":
            parser = CrawlDBParser(reader)
            builder.from_crawldb(parser, max_records=request.max_records)

        elif request.db_type.lower() == "linkdb":
            parser = LinkDBParser(reader)
            builder.from_linkdb(parser, max_records=request.max_records)

        elif request.db_type.lower() == "hostdb":
            # HostDB doesn't build a graph directly, just parse it
            parser = HostDBParser(reader)
            stats = parser.get_statistics(max_records=request.max_records)
            return StatusResponse(
                status="success",
                message=f"HostDB data loaded successfully",
                data={"statistics": stats},
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unknown db_type: {request.db_type}")

        # Store graph with dataset name
        graph = builder.get_graph()
        dataset_name = request.db_type.lower()
        metadata = {
            "db_type": request.db_type,
            "path": request.path,
            "storage": request.storage,
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges(),
        }
        
        add_dataset(dataset_name, graph, builder, metadata)

        return StatusResponse(
            status="success",
            message=f"Graph loaded successfully from {request.db_type}",
            data=metadata,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load graph: {str(e)}")


@app.get("/api/graph/summary", response_model=GraphSummary)
async def get_graph_summary():
    """Get graph summary statistics.

    Returns:
        GraphSummary: Graph statistics
    """
    current_graph = get_active_graph()
    if current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded")

    current_graph_builder = get_active_builder()
    if current_graph_builder is None:
        raise HTTPException(status_code=500, detail="Graph builder not initialized")

    stats = current_graph_builder.get_statistics()
    return GraphSummary(**stats)


@app.get("/api/graph/nodes")
async def get_nodes(
    limit: int = Query(100, description="Maximum number of nodes to return"),
    offset: int = Query(0, description="Offset for pagination"),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """Get graph nodes with pagination.

    Args:
        limit: Maximum nodes to return
        offset: Pagination offset
        status: Optional status filter

    Returns:
        Dict: Nodes data
    """
    current_graph = get_active_graph()
    if current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded")

    nodes = []
    count = 0
    skip_count = 0

    for node_id, attrs in current_graph.nodes(data=True):
        # Apply status filter
        if status and attrs.get("status") != status:
            continue

        # Apply pagination
        if skip_count < offset:
            skip_count += 1
            continue

        if count >= limit:
            break

        nodes.append({"id": node_id, "attributes": attrs})
        count += 1

    return {
        "nodes": nodes,
        "total": current_graph.number_of_nodes(),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/graph/edges")
async def get_edges(
    limit: int = Query(100, description="Maximum number of edges to return"),
    offset: int = Query(0, description="Offset for pagination"),
):
    """Get graph edges with pagination.

    Args:
        limit: Maximum edges to return
        offset: Pagination offset

    Returns:
        Dict: Edges data
    """
    current_graph = get_active_graph()
    if current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded")

    edges = []
    count = 0
    skip_count = 0

    for source, target, attrs in current_graph.edges(data=True):
        # Apply pagination
        if skip_count < offset:
            skip_count += 1
            continue

        if count >= limit:
            break

        edges.append({"source": source, "target": target, "attributes": attrs})
        count += 1

    return {
        "edges": edges,
        "total": current_graph.number_of_edges(),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/graph/data", response_model=GraphDataResponse)
async def get_graph_data(
    max_nodes: Optional[int] = Query(None, description="Maximum nodes to include"),
    format: str = Query("json", description="Export format: json or sigma"),
):
    """Get complete graph data for visualization.

    Args:
        max_nodes: Maximum nodes to include
        format: Export format

    Returns:
        GraphDataResponse: Complete graph data
    """
    current_graph = get_active_graph()
    if current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded")

    exporter = GraphExporter(current_graph)

    if format == "sigma":
        data = exporter.to_sigma_json(max_nodes=max_nodes)
    else:
        data = exporter.to_json(max_nodes=max_nodes, include_positions=True)

    # Add metadata to the response
    data["metadata"] = get_active_metadata()

    return GraphDataResponse(**data)


@app.post("/api/graph/filter")
async def filter_graph(request: FilterRequest):
    """Filter graph by criteria.

    Args:
        request: Filter request

    Returns:
        Dict: Filtered graph statistics
    """
    current_graph = get_active_graph()
    current_graph_builder = get_active_builder()
    
    if current_graph is None or current_graph_builder is None:
        raise HTTPException(status_code=404, detail="No graph loaded")

    try:
        if request.filter_type == "status":
            filtered = current_graph_builder.filter_by_status(request.value)
        elif request.filter_type == "domain":
            filtered = current_graph_builder.filter_by_domain(request.value)
        elif request.filter_type == "score":
            filtered = current_graph_builder.filter_by_score(
                request.value, request.max_value
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown filter type: {request.filter_type}"
            )

        return {
            "status": "success",
            "filtered_nodes": filtered.number_of_nodes(),
            "filtered_edges": filtered.number_of_edges(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filter failed: {str(e)}")


@app.post("/api/graph/export")
async def export_graph(request: ExportRequest):
    """Export graph in specified format.

    Args:
        request: Export request

    Returns:
        Dict: Exported graph data
    """
    current_graph = get_active_graph()
    if current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded")

    exporter = GraphExporter(current_graph)

    try:
        if request.include_clustering:
            data = exporter.export_with_clustering(max_nodes=request.max_nodes)
        elif request.format == "sigma":
            data = exporter.to_sigma_json(max_nodes=request.max_nodes)
        elif request.format == "json":
            data = exporter.to_json(max_nodes=request.max_nodes, include_positions=True)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown format: {request.format}")

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.post("/api/graph/analyze")
async def analyze_graph(request: AnalysisRequest):
    """Run graph analysis.

    Args:
        request: Analysis request

    Returns:
        Dict: Analysis results
    """
    current_graph = get_active_graph()
    current_graph_builder = get_active_builder()
    
    if current_graph is None or current_graph_builder is None:
        raise HTTPException(status_code=404, detail="No graph loaded")

    try:
        if request.analysis_type == "pagerank":
            alpha = request.params.get("alpha", 0.85) if request.params else 0.85
            results = current_graph_builder.calculate_pagerank(alpha=alpha)
            top_nodes = sorted(results.items(), key=lambda x: x[1], reverse=True)[:10]
            return {"type": "pagerank", "top_nodes": top_nodes}

        elif request.analysis_type == "centrality":
            centrality_type = (
                request.params.get("type", "in_degree") if request.params else "in_degree"
            )
            if centrality_type == "in_degree":
                results = current_graph_builder.calculate_in_degree_centrality()
            else:
                results = current_graph_builder.calculate_out_degree_centrality()

            top_nodes = sorted(results.items(), key=lambda x: x[1], reverse=True)[:10]
            return {"type": f"{centrality_type}_centrality", "top_nodes": top_nodes}

        elif request.analysis_type == "components":
            strong = current_graph_builder.find_strongly_connected_components()
            weak = current_graph_builder.find_weakly_connected_components()
            return {
                "type": "components",
                "num_strongly_connected": len(strong),
                "num_weakly_connected": len(weak),
                "largest_component_size": len(max(strong, key=len)) if strong else 0,
            }

        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown analysis type: {request.analysis_type}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/search")
async def search_nodes(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum results"),
):
    """Search for nodes by URL.

    Args:
        q: Search query
        limit: Maximum results

    Returns:
        Dict: Search results
    """
    current_graph = get_active_graph()
    if current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded")

    results = []
    count = 0

    for node_id, attrs in current_graph.nodes(data=True):
        if q.lower() in node_id.lower():
            results.append({"id": node_id, "attributes": attrs})
            count += 1
            if count >= limit:
                break

    return {"results": results, "total": len(results), "query": q}


@app.get("/api/config/hdfs")
async def get_hdfs_config():
    """Get current HDFS configuration.

    Returns:
        Dict: HDFS configuration
    """
    return {
        "namenode": config.hdfs_namenode,
        "port": config.hdfs_port,
        "hadoop_conf_dir": config.hadoop_conf_dir,
    }


@app.get("/api/hosts")
async def get_host_statistics():
    """Get host-level aggregations from graph.

    Returns:
        Dict: Host statistics
    """
    current_graph = get_active_graph()
    current_graph_builder = get_active_builder()
    
    if current_graph is None or current_graph_builder is None:
        raise HTTPException(status_code=404, detail="No graph loaded")

    try:
        # Extract host-level graph
        host_graph = current_graph_builder.extract_host_graph()

        # Calculate host statistics
        host_stats = []
        for host in host_graph.nodes():
            in_degree = host_graph.in_degree(host)
            out_degree = host_graph.out_degree(host)
            host_stats.append(
                {
                    "host": host,
                    "in_degree": in_degree,
                    "out_degree": out_degree,
                    "total_degree": in_degree + out_degree,
                }
            )

        # Sort by total degree
        host_stats.sort(key=lambda x: x["total_degree"], reverse=True)

        return {
            "total_hosts": len(host_stats),
            "top_hosts": host_stats[:20],
            "host_graph_edges": host_graph.number_of_edges(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate host statistics: {str(e)}"
        )


# Mount static files for frontend (must be last, after all API routes)
# Determine the path to the frontend dist directory
FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists() and FRONTEND_DIST.is_dir():
    # Check if index.html exists
    if (FRONTEND_DIST / "index.html").exists():
        # Mount the frontend application at root
        # The html=True parameter enables SPA routing (serves index.html for all routes)
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
    else:
        # Frontend dist exists but no index.html - incomplete build
        @app.get("/")
        async def frontend_incomplete():
            return {
                "error": "Frontend incomplete",
                "message": "Frontend dist directory exists but index.html not found. Run 'npm run build' in frontend/",
                "api_docs": "/docs",
            }
else:
    # Frontend not built at all
    @app.get("/")
    async def frontend_not_built():
        return {
            "error": "Frontend not built",
            "message": "Run 'cd frontend && npm run build' to enable interactive visualization",
            "api_docs": "/docs",
            "api_status": "/api/status",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.api_host, port=config.api_port, reload=config.api_reload)
