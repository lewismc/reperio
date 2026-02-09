"""Tests for graph builder."""

import pytest
import networkx as nx

from reperio.graph.graph_builder import GraphBuilder
from reperio.parsers.crawldb_parser import CrawlDBParser
from reperio.parsers.linkdb_parser import LinkDBParser


class MockReader:
    """Mock reader for testing."""

    def __init__(self, records):
        self.records = records

    def read_records(self, max_records=None):
        count = 0
        for record in self.records:
            if max_records and count >= max_records:
                break
            yield record
            count += 1

    def close(self):
        pass


class TestGraphBuilder:
    """Test graph builder functionality."""

    def test_from_crawldb(self):
        """Test building graph from CrawlDB data."""
        mock_records = [
            {"key": "http://example.com", "value": {"status": 2, "score": 0.5}},
            {"key": "http://test.com", "value": {"status": 2, "score": 0.3}},
        ]

        reader = MockReader(mock_records)
        parser = CrawlDBParser(reader)
        builder = GraphBuilder()

        graph = builder.from_crawldb(parser)

        assert graph.number_of_nodes() == 2
        assert graph.has_node("http://example.com")
        assert graph.has_node("http://test.com")

    def test_from_linkdb(self):
        """Test building graph from LinkDB data."""
        mock_records = [
            {
                "key": "http://target.com",
                "value": {
                    "inlinks": [
                        {"from_url": "http://source.com", "anchor": "Link"},
                    ]
                },
            }
        ]

        reader = MockReader(mock_records)
        parser = LinkDBParser(reader)
        builder = GraphBuilder()

        graph = builder.from_linkdb(parser)

        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() == 1
        assert graph.has_edge("http://source.com", "http://target.com")

    def test_filter_by_status(self):
        """Test filtering graph by status."""
        mock_records = [
            {"key": "http://fetched.com", "value": {"status": 2, "score": 0.5}},
            {"key": "http://unfetched.com", "value": {"status": 1, "score": 0.3}},
        ]

        reader = MockReader(mock_records)
        parser = CrawlDBParser(reader)
        builder = GraphBuilder()
        builder.from_crawldb(parser)

        filtered = builder.filter_by_status("fetched")
        assert filtered.number_of_nodes() == 1
        assert filtered.has_node("http://fetched.com")

    def test_filter_by_score(self):
        """Test filtering graph by score range."""
        mock_records = [
            {"key": "http://high.com", "value": {"status": 2, "score": 0.8}},
            {"key": "http://low.com", "value": {"status": 2, "score": 0.2}},
        ]

        reader = MockReader(mock_records)
        parser = CrawlDBParser(reader)
        builder = GraphBuilder()
        builder.from_crawldb(parser)

        filtered = builder.filter_by_score(0.5)
        assert filtered.number_of_nodes() == 1
        assert filtered.has_node("http://high.com")

    def test_calculate_pagerank(self):
        """Test PageRank calculation."""
        builder = GraphBuilder()
        builder.graph.add_edge("A", "B")
        builder.graph.add_edge("B", "C")
        builder.graph.add_edge("C", "A")

        pagerank = builder.calculate_pagerank()
        assert len(pagerank) == 3
        assert all(0 <= score <= 1 for score in pagerank.values())

    def test_get_statistics(self):
        """Test getting graph statistics."""
        builder = GraphBuilder()
        builder.graph.add_node("A")
        builder.graph.add_node("B")
        builder.graph.add_edge("A", "B")

        stats = builder.get_statistics()
        assert stats["num_nodes"] == 2
        assert stats["num_edges"] == 1
        assert stats["is_directed"] is True

    def test_sample_graph(self):
        """Test graph sampling."""
        builder = GraphBuilder()
        for i in range(10):
            builder.graph.add_node(f"node_{i}")

        sampled = builder.sample_graph(5, method="random")
        assert sampled.number_of_nodes() == 5

    def test_extract_host_graph(self):
        """Test extracting host-level graph."""
        builder = GraphBuilder()
        builder.graph.add_edge("http://example.com/page1", "http://test.com/page2")
        builder.graph.add_edge("http://example.com/page3", "http://test.com/page4")

        host_graph = builder.extract_host_graph()
        assert host_graph.number_of_nodes() == 2
        assert host_graph.has_edge("example.com", "test.com")
        assert host_graph["example.com"]["test.com"]["weight"] == 2
