"""Pydantic models for API requests and responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LoadGraphRequest(BaseModel):
    """Request model for loading graph data."""

    path: str = Field(..., description="Path to Nutch data (local or HDFS)")
    db_type: str = Field(..., description="Database type: crawldb, linkdb, or hostdb")
    storage: str = Field(default="local", description="Storage type: local or hdfs")
    max_records: Optional[int] = Field(None, description="Maximum records to load")
    hdfs_config: Optional[Dict[str, Any]] = Field(
        None, description="HDFS configuration (namenode, port)"
    )


class HDFSConfig(BaseModel):
    """HDFS configuration model."""

    namenode: str = Field(..., description="HDFS namenode hostname")
    port: int = Field(default=9000, description="HDFS namenode port")
    hadoop_conf_dir: Optional[str] = Field(None, description="Path to Hadoop config directory")


class GraphSummary(BaseModel):
    """Graph summary statistics."""

    num_nodes: int
    num_edges: int
    density: float
    is_directed: bool
    num_strongly_connected_components: int
    num_weakly_connected_components: int


class NodeResponse(BaseModel):
    """Response model for node data."""

    id: str
    label: str
    attributes: Dict[str, Any]


class EdgeResponse(BaseModel):
    """Response model for edge data."""

    source: str
    target: str
    attributes: Dict[str, Any]


class GraphDataResponse(BaseModel):
    """Response model for graph data."""

    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ExportRequest(BaseModel):
    """Request model for graph export."""

    format: str = Field(..., description="Export format: json, sigma, gexf, graphml")
    max_nodes: Optional[int] = Field(None, description="Maximum nodes to export")
    include_clustering: bool = Field(False, description="Include community detection")


class FilterRequest(BaseModel):
    """Request model for filtering graph."""

    filter_type: str = Field(..., description="Filter type: status, domain, score")
    value: Any = Field(..., description="Filter value")
    max_value: Optional[Any] = Field(None, description="Maximum value (for range filters)")


class AnalysisRequest(BaseModel):
    """Request model for graph analysis."""

    analysis_type: str = Field(
        ..., description="Analysis type: pagerank, centrality, components"
    )
    params: Optional[Dict[str, Any]] = Field(None, description="Analysis parameters")


class StatusResponse(BaseModel):
    """Generic status response."""

    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
