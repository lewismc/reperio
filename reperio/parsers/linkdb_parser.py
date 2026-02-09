"""Parser for Apache Nutch LinkDB data."""

from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from reperio.readers.sequencefile_reader import NutchSequenceFileReader


class LinkDBParser:
    """Parser for LinkDB SequenceFiles.

    LinkDB stores information about inbound links (inlinks) to URLs,
    including source URLs and anchor text.
    """

    def __init__(self, reader: NutchSequenceFileReader):
        """Initialize LinkDB parser.

        Args:
            reader: SequenceFile reader for LinkDB
        """
        self.reader = reader

    def parse(self, max_records: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Parse LinkDB records.

        Args:
            max_records: Maximum number of records to parse (None for all)

        Yields:
            Dict: Parsed LinkDB entry with target URL and inlinks
        """
        for record in self.reader.read_records(max_records=max_records):
            parsed = self._parse_record(record)
            if parsed:
                yield parsed

    def _parse_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single LinkDB record.

        Args:
            record: Raw record from SequenceFile reader

        Returns:
            Dict: Parsed record or None if parsing fails
        """
        try:
            target_url = record.get("key", "")
            value = record.get("value", {})

            # Extract inlinks
            inlinks = value.get("inlinks", [])
            num_inlinks = value.get("num_inlinks", len(inlinks))

            # Build parsed record
            parsed = {
                "target_url": target_url,
                "num_inlinks": num_inlinks,
                "inlinks": inlinks,
            }

            # Add raw data if available
            if "raw" in value:
                parsed["raw"] = value["raw"]

            return parsed

        except Exception as e:
            # Return minimal record on error
            return {
                "target_url": record.get("key", "unknown"),
                "num_inlinks": 0,
                "inlinks": [],
                "error": str(e),
            }

    def get_edges(self, max_records: Optional[int] = None) -> Iterator[Tuple[str, str, Dict]]:
        """Extract graph edges from LinkDB.

        Args:
            max_records: Maximum number of records to process

        Yields:
            Tuple[str, str, Dict]: (source_url, target_url, edge_attributes)
        """
        for record in self.parse(max_records=max_records):
            target_url = record.get("target_url", "")

            for inlink in record.get("inlinks", []):
                source_url = inlink.get("from_url", "")
                anchor = inlink.get("anchor", "")

                if source_url and target_url:
                    yield (source_url, target_url, {"anchor": anchor})

    def get_statistics(self, max_records: Optional[int] = None) -> Dict[str, Any]:
        """Calculate statistics for LinkDB.

        Args:
            max_records: Maximum number of records to analyze (None for all)

        Returns:
            Dict: Statistics including inlink distribution, unique sources, etc.
        """
        total_targets = 0
        total_inlinks = 0
        inlink_counts = []
        unique_sources: Set[str] = set()

        for record in self.parse(max_records=max_records):
            total_targets += 1
            num_inlinks = record.get("num_inlinks", 0)
            total_inlinks += num_inlinks
            inlink_counts.append(num_inlinks)

            # Track unique source URLs
            for inlink in record.get("inlinks", []):
                source_url = inlink.get("from_url")
                if source_url:
                    unique_sources.add(source_url)

        # Calculate statistics
        avg_inlinks = total_inlinks / total_targets if total_targets > 0 else 0.0
        inlink_counts.sort()
        median_inlinks = inlink_counts[len(inlink_counts) // 2] if inlink_counts else 0

        return {
            "total_target_urls": total_targets,
            "total_inlinks": total_inlinks,
            "unique_source_urls": len(unique_sources),
            "avg_inlinks_per_url": avg_inlinks,
            "median_inlinks": median_inlinks,
            "max_inlinks": max(inlink_counts) if inlink_counts else 0,
        }

    def get_top_linked_urls(
        self, max_records: Optional[int] = None, top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get URLs with most inlinks.

        Args:
            max_records: Maximum number of records to analyze
            top_n: Number of top results to return

        Returns:
            List[Dict]: Top linked URLs with inlink counts
        """
        url_counts = []

        for record in self.parse(max_records=max_records):
            url_counts.append(
                {
                    "url": record.get("target_url"),
                    "inlink_count": record.get("num_inlinks", 0),
                }
            )

        # Sort by inlink count
        url_counts.sort(key=lambda x: x["inlink_count"], reverse=True)

        return url_counts[:top_n]

    def close(self):
        """Close the reader."""
        if self.reader:
            self.reader.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
