"""Graph exporter for visualization and external tools."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx


class GraphExporter:
    """Export NetworkX graphs to various formats for visualization."""

    def __init__(self, graph: nx.DiGraph):
        """Initialize graph exporter.

        Args:
            graph: NetworkX directed graph to export
        """
        self.graph = graph

    def to_json(
        self, max_nodes: Optional[int] = None, include_positions: bool = False
    ) -> Dict[str, Any]:
        """Export graph to JSON format for web visualization.

        Args:
            max_nodes: Maximum number of nodes to include (None for all)
            include_positions: Whether to pre-calculate node positions

        Returns:
            Dict: Graph data in JSON-serializable format
        """
        graph = self.graph
        if max_nodes and graph.number_of_nodes() > max_nodes:
            # Sample the graph if it's too large
            import random

            nodes = random.sample(list(graph.nodes()), max_nodes)
            graph = graph.subgraph(nodes).copy()

        # Build nodes list
        nodes = []
        for node_id, attrs in graph.nodes(data=True):
            node_data = {
                "id": node_id,
                "label": self._get_node_label(node_id, attrs),
                **attrs,
            }

            # Add position if requested
            if include_positions:
                pos = self._calculate_positions(graph)
                if node_id in pos:
                    node_data["x"] = pos[node_id][0]
                    node_data["y"] = pos[node_id][1]

            nodes.append(node_data)

        # Build edges list
        edges = []
        for source, target, attrs in graph.edges(data=True):
            edge_data = {
                "source": source,
                "target": target,
                **attrs,
            }
            edges.append(edge_data)

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "num_nodes": len(nodes),
                "num_edges": len(edges),
                "directed": graph.is_directed(),
            },
        }

    def to_sigma_json(self, max_nodes: Optional[int] = None) -> Dict[str, Any]:
        """Export graph to Sigma.js compatible JSON format.

        Args:
            max_nodes: Maximum number of nodes to include

        Returns:
            Dict: Sigma.js compatible graph data
        """
        graph = self.graph
        if max_nodes and graph.number_of_nodes() > max_nodes:
            import random

            nodes = random.sample(list(graph.nodes()), max_nodes)
            graph = graph.subgraph(nodes).copy()

        # Calculate positions
        pos = self._calculate_positions(graph)

        # Build nodes for Sigma.js
        nodes = []
        for node_id, attrs in graph.nodes(data=True):
            x, y = pos.get(node_id, (0, 0))

            node_data = {
                "key": str(node_id),
                "attributes": {
                    "label": self._get_node_label(node_id, attrs),
                    "x": float(x),
                    "y": float(y),
                    "size": self._calculate_node_size(node_id, graph),
                    "color": self._get_node_color(attrs),
                    **{k: v for k, v in attrs.items() if k != "node_type"},
                },
            }
            nodes.append(node_data)

        # Build edges for Sigma.js
        edges = []
        for idx, (source, target, attrs) in enumerate(graph.edges(data=True)):
            edge_data = {
                "key": f"e{idx}",
                "source": str(source),
                "target": str(target),
                "attributes": {**attrs},
            }
            edges.append(edge_data)

        return {"nodes": nodes, "edges": edges}

    def to_gexf(self, output_path: str):
        """Export graph to GEXF format (for Gephi).

        Args:
            output_path: Path to output GEXF file
        """
        nx.write_gexf(self.graph, output_path)

    def to_graphml(self, output_path: str):
        """Export graph to GraphML format.

        Args:
            output_path: Path to output GraphML file
        """
        nx.write_graphml(self.graph, output_path)

    def to_json_file(self, output_path: str, max_nodes: Optional[int] = None, **kwargs):
        """Export graph to JSON file.

        Args:
            output_path: Path to output JSON file
            max_nodes: Maximum number of nodes to include
            **kwargs: Additional arguments for to_json()
        """
        data = self.to_json(max_nodes=max_nodes, **kwargs)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def to_sigma_json_file(self, output_path: str, max_nodes: Optional[int] = None):
        """Export graph to Sigma.js JSON file.

        Args:
            output_path: Path to output JSON file
            max_nodes: Maximum number of nodes to include
        """
        data = self.to_sigma_json(max_nodes=max_nodes)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def export_with_clustering(
        self, num_clusters: int = 10, max_nodes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Export graph with community detection/clustering.

        Args:
            num_clusters: Target number of clusters
            max_nodes: Maximum number of nodes to include

        Returns:
            Dict: Graph data with cluster assignments
        """
        import networkx.algorithms.community as nx_comm

        graph = self.graph
        if max_nodes and graph.number_of_nodes() > max_nodes:
            import random

            nodes = random.sample(list(graph.nodes()), max_nodes)
            graph = graph.subgraph(nodes).copy()

        # Detect communities (using Louvain method via greedy modularity)
        undirected = graph.to_undirected()
        communities = nx_comm.greedy_modularity_communities(undirected)

        # Assign cluster IDs to nodes
        node_to_cluster = {}
        for cluster_id, community in enumerate(communities):
            for node in community:
                node_to_cluster[node] = cluster_id

        # Export with cluster information
        data = self.to_json(max_nodes=None)

        # Add cluster info to nodes
        for node in data["nodes"]:
            node["cluster"] = node_to_cluster.get(node["id"], -1)

        data["metadata"]["num_clusters"] = len(communities)

        return data

    def _calculate_positions(self, graph: nx.DiGraph) -> Dict[str, tuple]:
        """Calculate node positions using spring layout.

        Args:
            graph: Graph to layout

        Returns:
            Dict: Node positions {node_id: (x, y)}
        """
        try:
            # Use spring layout for positioning
            if graph.number_of_nodes() > 1000:
                # Use faster layout for large graphs
                pos = nx.spring_layout(graph, k=0.5, iterations=20)
            else:
                pos = nx.spring_layout(graph, k=1, iterations=50)

            # Scale positions for visualization (multiply by 1000 for pixel coordinates)
            return {node: (x * 1000, y * 1000) for node, (x, y) in pos.items()}

        except Exception:
            # Fallback to random positions if layout fails
            import random

            return {
                node: (random.uniform(-500, 500), random.uniform(-500, 500))
                for node in graph.nodes()
            }

    def _get_node_label(self, node_id: str, attrs: Dict) -> str:
        """Get display label for a node.

        Args:
            node_id: Node identifier
            attrs: Node attributes

        Returns:
            str: Display label
        """
        # Try to extract domain/path from URL
        from urllib.parse import urlparse

        try:
            parsed = urlparse(node_id)
            if parsed.netloc:
                # Show domain + path (truncated)
                path = parsed.path[:30] if len(parsed.path) > 30 else parsed.path
                return f"{parsed.netloc}{path}"
        except Exception:
            pass

        # Truncate long IDs
        if len(node_id) > 50:
            return node_id[:47] + "..."

        return node_id

    def _calculate_node_size(self, node_id: str, graph: nx.DiGraph) -> float:
        """Calculate node size based on degree.

        Args:
            node_id: Node identifier
            graph: Graph

        Returns:
            float: Node size
        """
        degree = graph.degree(node_id)
        # Scale between 1 and 10
        return max(1, min(10, degree / 2))

    def _get_node_color(self, attrs: Dict) -> str:
        """Get node color based on attributes.

        Args:
            attrs: Node attributes

        Returns:
            str: Hex color code
        """
        status = attrs.get("status", "unknown")

        # Color by status
        color_map = {
            "fetched": "#4CAF50",  # Green
            "unfetched": "#FFC107",  # Amber
            "error": "#F44336",  # Red
            "redirect_temp": "#2196F3",  # Blue
            "redirect_perm": "#3F51B5",  # Indigo
            "gone": "#9E9E9E",  # Grey
            "unknown": "#607D8B",  # Blue Grey
        }

        return color_map.get(status, "#757575")

    def export_subgraph_by_depth(
        self, root_node: str, max_depth: int = 2, direction: str = "out"
    ) -> Dict[str, Any]:
        """Export subgraph around a root node up to a certain depth.

        Args:
            root_node: Starting node
            max_depth: Maximum depth to traverse
            direction: Direction to traverse ('out', 'in', or 'both')

        Returns:
            Dict: Subgraph data
        """
        if root_node not in self.graph:
            return {"nodes": [], "edges": [], "metadata": {"error": "Root node not found"}}

        # Collect nodes at each depth level
        nodes_to_include = {root_node}
        current_level = {root_node}

        for depth in range(max_depth):
            next_level = set()

            for node in current_level:
                if direction in ("out", "both"):
                    next_level.update(self.graph.successors(node))
                if direction in ("in", "both"):
                    next_level.update(self.graph.predecessors(node))

            nodes_to_include.update(next_level)
            current_level = next_level

        # Create subgraph
        subgraph = self.graph.subgraph(nodes_to_include).copy()

        # Export
        self_temp = GraphExporter(subgraph)
        return self_temp.to_json(include_positions=True)
