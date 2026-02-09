"""Graph builder for Apache Nutch data structures."""

import re
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urlparse

import networkx as nx

from reperio.parsers.crawldb_parser import CrawlDBParser
from reperio.parsers.linkdb_parser import LinkDBParser


class GraphBuilder:
    """Build NetworkX graphs from Nutch data structures.

    This class converts parsed Nutch data (CrawlDB, LinkDB) into
    NetworkX directed graphs for analysis and visualization.
    """

    def __init__(self):
        """Initialize graph builder."""
        self.graph = nx.DiGraph()
        self._node_count = 0
        self._edge_count = 0

    def from_crawldb(
        self,
        parser: CrawlDBParser,
        max_records: Optional[int] = None,
        filter_fn: Optional[Callable[[Dict], bool]] = None,
    ) -> nx.DiGraph:
        """Build graph from CrawlDB data.

        Args:
            parser: CrawlDB parser
            max_records: Maximum number of records to process
            filter_fn: Optional filter function for records

        Returns:
            nx.DiGraph: Graph with nodes from CrawlDB
        """
        for record in parser.parse(max_records=max_records):
            # Apply filter if provided
            if filter_fn and not filter_fn(record):
                continue

            url = record.get("url", "")
            if not url:
                continue

            # Add node with attributes
            self.graph.add_node(
                url,
                status=record.get("status", "unknown"),
                status_code=record.get("status_code", 0),
                score=record.get("score", 0.0),
                fetch_time=record.get("fetch_time", 0),
                fetch_datetime=record.get("fetch_datetime"),
                retries=record.get("retries", 0),
                fetch_interval=record.get("fetch_interval", 0),
                node_type="url",
            )
            self._node_count += 1

        return self.graph

    def from_linkdb(
        self,
        parser: LinkDBParser,
        max_records: Optional[int] = None,
        filter_fn: Optional[Callable[[Dict], bool]] = None,
    ) -> nx.DiGraph:
        """Build graph from LinkDB data.

        Args:
            parser: LinkDB parser
            max_records: Maximum number of records to process
            filter_fn: Optional filter function for edges

        Returns:
            nx.DiGraph: Graph with edges from LinkDB
        """
        for source, target, attrs in parser.get_edges(max_records=max_records):
            # Apply filter if provided
            if filter_fn and not filter_fn({"source": source, "target": target, **attrs}):
                continue

            if not source or not target:
                continue

            # Add nodes if they don't exist
            if not self.graph.has_node(source):
                self.graph.add_node(source, node_type="url")
                self._node_count += 1

            if not self.graph.has_node(target):
                self.graph.add_node(target, node_type="url")
                self._node_count += 1

            # Add edge
            self.graph.add_edge(source, target, anchor=attrs.get("anchor", ""))
            self._edge_count += 1

        return self.graph

    def from_combined(
        self,
        crawldb_parser: CrawlDBParser,
        linkdb_parser: LinkDBParser,
        max_records: Optional[int] = None,
    ) -> nx.DiGraph:
        """Build graph combining CrawlDB and LinkDB data.

        Args:
            crawldb_parser: CrawlDB parser for node attributes
            linkdb_parser: LinkDB parser for edges
            max_records: Maximum number of records to process

        Returns:
            nx.DiGraph: Combined graph
        """
        # First, add nodes with attributes from CrawlDB
        self.from_crawldb(crawldb_parser, max_records=max_records)

        # Then, add edges from LinkDB
        self.from_linkdb(linkdb_parser, max_records=max_records)

        return self.graph

    def filter_by_status(self, status: str) -> nx.DiGraph:
        """Filter graph nodes by crawl status.

        Args:
            status: Status name to filter by

        Returns:
            nx.DiGraph: Filtered subgraph
        """
        nodes_to_keep = [
            node for node, attrs in self.graph.nodes(data=True) if attrs.get("status") == status
        ]

        return self.graph.subgraph(nodes_to_keep).copy()

    def filter_by_domain(self, domain_pattern: str) -> nx.DiGraph:
        """Filter graph nodes by domain pattern.

        Args:
            domain_pattern: Domain regex pattern to match

        Returns:
            nx.DiGraph: Filtered subgraph
        """
        pattern = re.compile(domain_pattern)
        nodes_to_keep = []

        for node in self.graph.nodes():
            try:
                parsed = urlparse(node)
                domain = parsed.netloc
                if pattern.search(domain):
                    nodes_to_keep.append(node)
            except Exception:
                continue

        return self.graph.subgraph(nodes_to_keep).copy()

    def filter_by_score(self, min_score: float, max_score: Optional[float] = None) -> nx.DiGraph:
        """Filter graph nodes by score range.

        Args:
            min_score: Minimum score threshold
            max_score: Maximum score threshold (None for no upper limit)

        Returns:
            nx.DiGraph: Filtered subgraph
        """
        nodes_to_keep = []

        for node, attrs in self.graph.nodes(data=True):
            score = attrs.get("score", 0.0)
            if score >= min_score:
                if max_score is None or score <= max_score:
                    nodes_to_keep.append(node)

        return self.graph.subgraph(nodes_to_keep).copy()

    def calculate_pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        """Calculate PageRank for all nodes.

        Args:
            alpha: Damping parameter (default: 0.85)

        Returns:
            Dict[str, float]: PageRank scores for each node
        """
        return nx.pagerank(self.graph, alpha=alpha)

    def calculate_in_degree_centrality(self) -> Dict[str, float]:
        """Calculate in-degree centrality.

        Returns:
            Dict[str, float]: In-degree centrality for each node
        """
        return nx.in_degree_centrality(self.graph)

    def calculate_out_degree_centrality(self) -> Dict[str, float]:
        """Calculate out-degree centrality.

        Returns:
            Dict[str, float]: Out-degree centrality for each node
        """
        return nx.out_degree_centrality(self.graph)

    def find_strongly_connected_components(self) -> List[Set[str]]:
        """Find strongly connected components.

        Returns:
            List[Set[str]]: List of strongly connected component node sets
        """
        return list(nx.strongly_connected_components(self.graph))

    def find_weakly_connected_components(self) -> List[Set[str]]:
        """Find weakly connected components.

        Returns:
            List[Set[str]]: List of weakly connected component node sets
        """
        return list(nx.weakly_connected_components(self.graph))

    def get_top_nodes_by_pagerank(self, n: int = 10) -> List[tuple]:
        """Get top N nodes by PageRank.

        Args:
            n: Number of top nodes to return

        Returns:
            List[tuple]: List of (node, pagerank_score) tuples
        """
        pagerank = self.calculate_pagerank()
        sorted_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:n]

    def get_top_nodes_by_indegree(self, n: int = 10) -> List[tuple]:
        """Get top N nodes by in-degree.

        Args:
            n: Number of top nodes to return

        Returns:
            List[tuple]: List of (node, in_degree) tuples
        """
        in_degrees = dict(self.graph.in_degree())
        sorted_nodes = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:n]

    def extract_host_graph(self) -> nx.DiGraph:
        """Extract host-level graph from URL graph.

        Returns:
            nx.DiGraph: Host-level graph
        """
        host_graph = nx.DiGraph()

        # Add edges between hosts
        for source, target in self.graph.edges():
            try:
                source_host = urlparse(source).netloc
                target_host = urlparse(target).netloc

                if source_host and target_host and source_host != target_host:
                    if host_graph.has_edge(source_host, target_host):
                        host_graph[source_host][target_host]["weight"] += 1
                    else:
                        host_graph.add_edge(source_host, target_host, weight=1)

            except Exception:
                continue

        return host_graph

    def sample_graph(self, sample_size: int, method: str = "random") -> nx.DiGraph:
        """Sample nodes from the graph.

        Args:
            sample_size: Number of nodes to sample
            method: Sampling method ('random', 'pagerank', 'degree')

        Returns:
            nx.DiGraph: Sampled subgraph
        """
        if sample_size >= self.graph.number_of_nodes():
            return self.graph.copy()

        if method == "random":
            import random

            nodes = random.sample(list(self.graph.nodes()), sample_size)

        elif method == "pagerank":
            pagerank = self.calculate_pagerank()
            sorted_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
            nodes = [node for node, _ in sorted_nodes[:sample_size]]

        elif method == "degree":
            degrees = dict(self.graph.degree())
            sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
            nodes = [node for node, _ in sorted_nodes[:sample_size]]

        else:
            raise ValueError(f"Unknown sampling method: {method}")

        return self.graph.subgraph(nodes).copy()

    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics.

        Returns:
            Dict: Graph statistics
        """
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_directed": self.graph.is_directed(),
            "num_strongly_connected_components": nx.number_strongly_connected_components(
                self.graph
            )
            if self.graph.number_of_nodes() > 0
            else 0,
            "num_weakly_connected_components": nx.number_weakly_connected_components(self.graph)
            if self.graph.number_of_nodes() > 0
            else 0,
        }

    def get_graph(self) -> nx.DiGraph:
        """Get the current graph.

        Returns:
            nx.DiGraph: The graph
        """
        return self.graph

    def clear(self):
        """Clear the graph."""
        self.graph.clear()
        self._node_count = 0
        self._edge_count = 0
