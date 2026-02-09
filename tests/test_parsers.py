"""Tests for Nutch data parsers."""

import pytest

from reperio.parsers.crawldb_parser import CrawlDBParser
from reperio.parsers.linkdb_parser import LinkDBParser
from reperio.parsers.hostdb_parser import HostDBParser


class MockReader:
    """Mock SequenceFile reader for testing."""

    def __init__(self, records):
        self.records = records

    def read_records(self, max_records=None):
        """Yield mock records."""
        count = 0
        for record in self.records:
            if max_records and count >= max_records:
                break
            yield record
            count += 1

    def close(self):
        """Close mock reader."""
        pass


class TestCrawlDBParser:
    """Test CrawlDB parser."""

    def test_parse_basic_record(self):
        """Test parsing basic CrawlDB record."""
        mock_records = [
            {
                "key": "http://example.com",
                "value": {
                    "status": 2,
                    "fetch_time": 1609459200000,
                    "score": 0.5,
                    "retries": 0,
                    "fetch_interval": 2592000,
                },
            }
        ]

        reader = MockReader(mock_records)
        parser = CrawlDBParser(reader)

        records = list(parser.parse())
        assert len(records) == 1

        record = records[0]
        assert record["url"] == "http://example.com"
        assert record["status"] == "fetched"
        assert record["score"] == 0.5

    def test_parse_multiple_records(self):
        """Test parsing multiple CrawlDB records."""
        mock_records = [
            {"key": "http://example.com", "value": {"status": 2, "score": 0.5}},
            {"key": "http://test.com", "value": {"status": 1, "score": 0.3}},
        ]

        reader = MockReader(mock_records)
        parser = CrawlDBParser(reader)

        records = list(parser.parse())
        assert len(records) == 2

    def test_status_names(self):
        """Test status code to name mapping."""
        assert CrawlDBParser.STATUS_NAMES[1] == "unfetched"
        assert CrawlDBParser.STATUS_NAMES[2] == "fetched"
        assert CrawlDBParser.STATUS_NAMES[3] == "gone"


class TestLinkDBParser:
    """Test LinkDB parser."""

    def test_parse_basic_record(self):
        """Test parsing basic LinkDB record."""
        mock_records = [
            {
                "key": "http://target.com",
                "value": {
                    "num_inlinks": 2,
                    "inlinks": [
                        {"from_url": "http://source1.com", "anchor": "Link 1"},
                        {"from_url": "http://source2.com", "anchor": "Link 2"},
                    ],
                },
            }
        ]

        reader = MockReader(mock_records)
        parser = LinkDBParser(reader)

        records = list(parser.parse())
        assert len(records) == 1

        record = records[0]
        assert record["target_url"] == "http://target.com"
        assert record["num_inlinks"] == 2
        assert len(record["inlinks"]) == 2

    def test_get_edges(self):
        """Test extracting edges from LinkDB."""
        mock_records = [
            {
                "key": "http://target.com",
                "value": {
                    "inlinks": [
                        {"from_url": "http://source.com", "anchor": "Link"},
                    ],
                },
            }
        ]

        reader = MockReader(mock_records)
        parser = LinkDBParser(reader)

        edges = list(parser.get_edges())
        assert len(edges) == 1

        source, target, attrs = edges[0]
        assert source == "http://source.com"
        assert target == "http://target.com"
        assert attrs["anchor"] == "Link"


class TestHostDBParser:
    """Test HostDB parser."""

    def test_parse_basic_record(self):
        """Test parsing basic HostDB record."""
        mock_records = [
            {
                "key": "example.com",
                "value": {
                    "metadata": {
                        "homepage": "http://example.com",
                        "fetched": "100",
                        "unfetched": "50",
                    }
                },
            }
        ]

        reader = MockReader(mock_records)
        parser = HostDBParser(reader)

        records = list(parser.parse())
        assert len(records) == 1

        record = records[0]
        assert record["host"] == "example.com"
        assert record["homepage"] == "http://example.com"
        assert record["fetched"] == 100
        assert record["unfetched"] == 50

    def test_safe_int_conversion(self):
        """Test safe integer conversion."""
        parser = HostDBParser(MockReader([]))
        
        assert parser._safe_int("123") == 123
        assert parser._safe_int("invalid") == 0
        assert parser._safe_int(None) == 0

    def test_safe_float_conversion(self):
        """Test safe float conversion."""
        parser = HostDBParser(MockReader([]))
        
        assert parser._safe_float("123.45") == 123.45
        assert parser._safe_float("invalid") == 0.0
        assert parser._safe_float(None) == 0.0
