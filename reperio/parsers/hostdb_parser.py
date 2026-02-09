"""Parser for Apache Nutch HostDB data."""

from typing import Any, Dict, Iterator, List, Optional

from reperio.readers.sequencefile_reader import NutchSequenceFileReader


class HostDBParser:
    """Parser for HostDB SequenceFiles.

    HostDB stores host-level statistics aggregated from CrawlDB,
    including DNS info, homepage URLs, and response metrics.
    """

    def __init__(self, reader: NutchSequenceFileReader):
        """Initialize HostDB parser.

        Args:
            reader: SequenceFile reader for HostDB
        """
        self.reader = reader

    def parse(self, max_records: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Parse HostDB records.

        Args:
            max_records: Maximum number of records to parse (None for all)

        Yields:
            Dict: Parsed HostDB entry with host and statistics
        """
        for record in self.reader.read_records(max_records=max_records):
            parsed = self._parse_record(record)
            if parsed:
                yield parsed

    def _parse_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single HostDB record.

        Args:
            record: Raw record from SequenceFile reader

        Returns:
            Dict: Parsed record or None if parsing fails
        """
        try:
            host = record.get("key", "")
            value = record.get("value", {})

            # Extract metadata
            metadata = value.get("metadata", {})

            # Common HostDB metadata fields
            parsed = {
                "host": host,
                "homepage": metadata.get("homepage", ""),
                "dns_failures": self._safe_int(metadata.get("dnsFailures", "0")),
                "connection_failures": self._safe_int(metadata.get("connectionFailures", "0")),
                "unfetched": self._safe_int(metadata.get("unfetched", "0")),
                "fetched": self._safe_int(metadata.get("fetched", "0")),
                "not_modified": self._safe_int(metadata.get("notModified", "0")),
                "redirects_temp": self._safe_int(metadata.get("redirectsTemp", "0")),
                "redirects_perm": self._safe_int(metadata.get("redirectsPerm", "0")),
                "errors_404": self._safe_int(metadata.get("errors404", "0")),
                "errors_other": self._safe_int(metadata.get("errorsOther", "0")),
                "avg_response_time": self._safe_float(metadata.get("avgResponseTime", "0")),
                "metadata": metadata,
            }

            # Add raw data if available
            if "raw" in value:
                parsed["raw"] = value["raw"]

            return parsed

        except Exception as e:
            # Return minimal record on error
            return {
                "host": record.get("key", "unknown"),
                "error": str(e),
            }

    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert value to int.

        Args:
            value: Value to convert
            default: Default value if conversion fails

        Returns:
            int: Converted value or default
        """
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float.

        Args:
            value: Value to convert
            default: Default value if conversion fails

        Returns:
            float: Converted value or default
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_statistics(self, max_records: Optional[int] = None) -> Dict[str, Any]:
        """Calculate statistics for HostDB.

        Args:
            max_records: Maximum number of records to analyze (None for all)

        Returns:
            Dict: Aggregated statistics across all hosts
        """
        total_hosts = 0
        total_urls = 0
        total_fetched = 0
        total_errors = 0
        total_dns_failures = 0
        response_times = []

        for record in self.parse(max_records=max_records):
            total_hosts += 1
            total_fetched += record.get("fetched", 0)
            total_urls += record.get("unfetched", 0) + record.get("fetched", 0)
            total_errors += record.get("errors_404", 0) + record.get("errors_other", 0)
            total_dns_failures += record.get("dns_failures", 0)

            avg_response = record.get("avg_response_time", 0.0)
            if avg_response > 0:
                response_times.append(avg_response)

        # Calculate averages
        avg_urls_per_host = total_urls / total_hosts if total_hosts > 0 else 0.0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

        return {
            "total_hosts": total_hosts,
            "total_urls": total_urls,
            "total_fetched": total_fetched,
            "total_errors": total_errors,
            "total_dns_failures": total_dns_failures,
            "avg_urls_per_host": avg_urls_per_host,
            "avg_response_time": avg_response_time,
        }

    def get_top_hosts_by_urls(
        self, max_records: Optional[int] = None, top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get hosts with most URLs.

        Args:
            max_records: Maximum number of records to analyze
            top_n: Number of top results to return

        Returns:
            List[Dict]: Top hosts by URL count
        """
        host_stats = []

        for record in self.parse(max_records=max_records):
            url_count = record.get("unfetched", 0) + record.get("fetched", 0)
            host_stats.append(
                {
                    "host": record.get("host"),
                    "url_count": url_count,
                    "fetched": record.get("fetched", 0),
                    "errors": record.get("errors_404", 0) + record.get("errors_other", 0),
                }
            )

        # Sort by URL count
        host_stats.sort(key=lambda x: x["url_count"], reverse=True)

        return host_stats[:top_n]

    def get_problematic_hosts(
        self, max_records: Optional[int] = None, error_threshold: int = 10
    ) -> List[Dict[str, Any]]:
        """Get hosts with high error rates.

        Args:
            max_records: Maximum number of records to analyze
            error_threshold: Minimum number of errors to be considered problematic

        Returns:
            List[Dict]: Hosts with high error counts
        """
        problematic = []

        for record in self.parse(max_records=max_records):
            total_errors = (
                record.get("errors_404", 0)
                + record.get("errors_other", 0)
                + record.get("dns_failures", 0)
                + record.get("connection_failures", 0)
            )

            if total_errors >= error_threshold:
                problematic.append(
                    {
                        "host": record.get("host"),
                        "total_errors": total_errors,
                        "dns_failures": record.get("dns_failures", 0),
                        "connection_failures": record.get("connection_failures", 0),
                        "errors_404": record.get("errors_404", 0),
                        "errors_other": record.get("errors_other", 0),
                    }
                )

        # Sort by error count
        problematic.sort(key=lambda x: x["total_errors"], reverse=True)

        return problematic

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
