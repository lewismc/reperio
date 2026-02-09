"""Parser for Apache Nutch CrawlDB data."""

from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

from reperio.readers.sequencefile_reader import NutchSequenceFileReader


class CrawlDBParser:
    """Parser for CrawlDB SequenceFiles.

    CrawlDB stores information about crawled URLs including fetch status,
    scores, retry counts, and metadata.
    """

    # CrawlDatum status codes
    STATUS_DB_UNFETCHED = 1
    STATUS_DB_FETCHED = 2
    STATUS_DB_GONE = 3
    STATUS_DB_REDIR_TEMP = 4
    STATUS_DB_REDIR_PERM = 5
    STATUS_DB_NOTMODIFIED = 6
    STATUS_DB_DUPLICATE = 7
    STATUS_DB_ORPHAN = 8

    STATUS_NAMES = {
        STATUS_DB_UNFETCHED: "unfetched",
        STATUS_DB_FETCHED: "fetched",
        STATUS_DB_GONE: "gone",
        STATUS_DB_REDIR_TEMP: "redirect_temp",
        STATUS_DB_REDIR_PERM: "redirect_perm",
        STATUS_DB_NOTMODIFIED: "not_modified",
        STATUS_DB_DUPLICATE: "duplicate",
        STATUS_DB_ORPHAN: "orphan",
    }

    def __init__(self, reader: NutchSequenceFileReader):
        """Initialize CrawlDB parser.

        Args:
            reader: SequenceFile reader for CrawlDB
        """
        self.reader = reader

    def parse(self, max_records: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Parse CrawlDB records.

        Args:
            max_records: Maximum number of records to parse (None for all)

        Yields:
            Dict: Parsed CrawlDB entry with URL and metadata
        """
        for record in self.reader.read_records(max_records=max_records):
            parsed = self._parse_record(record)
            if parsed:
                yield parsed

    def _parse_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single CrawlDB record.

        Args:
            record: Raw record from SequenceFile reader

        Returns:
            Dict: Parsed record or None if parsing fails
        """
        try:
            url = record.get("key", "")
            value = record.get("value", {})

            # Extract status
            status_code = value.get("status", 0)
            status_name = self.STATUS_NAMES.get(status_code, "unknown")

            # Extract fetch time
            fetch_time = value.get("fetch_time", 0)
            fetch_datetime = None
            if fetch_time > 0:
                try:
                    fetch_datetime = datetime.fromtimestamp(fetch_time / 1000.0).isoformat()
                except (ValueError, OSError):
                    fetch_datetime = None

            # Build parsed record
            parsed = {
                "url": url,
                "status_code": status_code,
                "status": status_name,
                "fetch_time": fetch_time,
                "fetch_datetime": fetch_datetime,
                "retries": value.get("retries", 0),
                "fetch_interval": value.get("fetch_interval", 0),
                "score": value.get("score", 0.0),
                "metadata": value.get("metadata", {}),
            }

            # Add raw data if available
            if "raw" in value:
                parsed["raw"] = value["raw"]

            return parsed

        except Exception as e:
            # Return minimal record on error
            return {
                "url": record.get("key", "unknown"),
                "status": "error",
                "error": str(e),
            }

    def get_statistics(self, max_records: Optional[int] = None) -> Dict[str, Any]:
        """Calculate statistics for CrawlDB.

        Args:
            max_records: Maximum number of records to analyze (None for all)

        Returns:
            Dict: Statistics including status counts, score distribution, etc.
        """
        status_counts = {}
        total_records = 0
        total_score = 0.0
        scores = []

        for record in self.parse(max_records=max_records):
            total_records += 1
            status = record.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

            score = record.get("score", 0.0)
            total_score += score
            scores.append(score)

        # Calculate score statistics
        avg_score = total_score / total_records if total_records > 0 else 0.0
        scores.sort()
        median_score = scores[len(scores) // 2] if scores else 0.0

        return {
            "total_records": total_records,
            "status_counts": status_counts,
            "avg_score": avg_score,
            "median_score": median_score,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
        }

    def get_urls_by_status(
        self, status: str, max_records: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get URLs filtered by status.

        Args:
            status: Status name to filter by
            max_records: Maximum number of records to return

        Returns:
            List[Dict]: Filtered records
        """
        filtered = []
        count = 0

        for record in self.parse():
            if record.get("status") == status:
                filtered.append(record)
                count += 1
                if max_records and count >= max_records:
                    break

        return filtered

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
