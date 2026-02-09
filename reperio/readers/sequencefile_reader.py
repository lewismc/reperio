"""SequenceFile reader for Apache Nutch data structures."""

import struct
from io import BytesIO
from typing import Any, Dict, Iterator, Optional

from reperio.readers.filesystem import FileSystemManager

try:
    from hadoop.io import SequenceFile as HadoopSequenceFile
    HADOOP_AVAILABLE = True
except ImportError:
    HADOOP_AVAILABLE = False


class NutchSequenceFileReader:
    """Reader for Hadoop SequenceFiles containing Nutch data.

    This reader supports streaming processing of SequenceFiles from both
    local filesystem and HDFS.
    """

    # SequenceFile format constants
    SEQUENCE_FILE_VERSION = b"SEQ\x06"
    KEY_CLASS_NAME = "key_class"
    VALUE_CLASS_NAME = "value_class"
    COMPRESSION = "compression"
    BLOCK_COMPRESSION = "block_compression"
    METADATA = "metadata"

    def __init__(
        self,
        file_path: str,
        db_type: str,
        fs_manager: Optional[FileSystemManager] = None,
    ):
        """Initialize SequenceFile reader.

        Args:
            file_path: Path to the SequenceFile (local or HDFS)
            db_type: Type of Nutch database (crawldb, linkdb, hostdb)
            fs_manager: Filesystem manager (will be created if not provided)
        """
        self.file_path = file_path
        self.db_type = db_type.lower()
        self.fs_manager = fs_manager or FileSystemManager.create(file_path)
        self._metadata: Optional[Dict[str, Any]] = None
        self._file_handle = None

    def _read_vint(self, stream: BytesIO) -> int:
        """Read a variable-length integer (Hadoop VInt format).

        Args:
            stream: Input stream

        Returns:
            int: Decoded integer value
        """
        first_byte = stream.read(1)
        if not first_byte:
            raise EOFError("End of stream while reading VInt")

        first = first_byte[0]
        length = self._decode_vint_size(first)

        if length == 1:
            return first

        # Read remaining bytes
        remaining = stream.read(length - 1)
        if len(remaining) != length - 1:
            raise EOFError("End of stream while reading VInt")

        value = first & 0x7F if first < 0 else first
        for byte in remaining:
            value = (value << 8) | byte

        return value if first >= 0 else -value

    def _decode_vint_size(self, value: int) -> int:
        """Decode the size of a VInt from its first byte.

        Args:
            value: First byte of VInt

        Returns:
            int: Number of bytes in the VInt
        """
        if value >= -112:
            return 1
        elif value < -120:
            return -119 - value
        else:
            return -111 - value

    def _read_vlong(self, stream: BytesIO) -> int:
        """Read a variable-length long (Hadoop VLong format).

        Args:
            stream: Input stream

        Returns:
            int: Decoded long value
        """
        # VLong uses same encoding as VInt
        return self._read_vint(stream)

    def _read_text(self, stream: BytesIO) -> str:
        """Read a UTF-8 encoded Text field (Hadoop Text format).

        Args:
            stream: Input stream

        Returns:
            str: Decoded text string
        """
        length = self._read_vint(stream)
        if length == 0:
            return ""

        data = stream.read(length)
        if len(data) != length:
            raise EOFError("End of stream while reading Text")

        return data.decode("utf-8", errors="replace")

    def _read_bytes(self, stream: BytesIO, length: int) -> bytes:
        """Read a fixed number of bytes.

        Args:
            stream: Input stream
            length: Number of bytes to read

        Returns:
            bytes: Read bytes
        """
        data = stream.read(length)
        if len(data) != length:
            raise EOFError(f"Expected {length} bytes, got {len(data)}")
        return data

    def _parse_header(self, file_handle) -> Dict[str, Any]:
        """Parse SequenceFile header.

        Args:
            file_handle: Open file handle

        Returns:
            Dict: Parsed header metadata
        """
        # Read version
        version = file_handle.read(4)
        if not version.startswith(b"SEQ"):
            raise ValueError(f"Not a valid SequenceFile: {self.file_path}")

        # Read key class name
        key_class_length = struct.unpack(">B", file_handle.read(1))[0]
        key_class = file_handle.read(key_class_length).decode("utf-8")

        # Read value class name
        value_class_length = struct.unpack(">B", file_handle.read(1))[0]
        value_class = file_handle.read(value_class_length).decode("utf-8")

        # Read compression info
        compression = struct.unpack(">?", file_handle.read(1))[0]
        block_compression = struct.unpack(">?", file_handle.read(1))[0]

        # Read compression codec (if compressed)
        compression_codec = None
        if compression:
            codec_length = struct.unpack(">B", file_handle.read(1))[0]
            compression_codec = file_handle.read(codec_length).decode("utf-8")

        # Read metadata
        metadata_count = struct.unpack(">I", file_handle.read(4))[0]
        metadata = {}
        for _ in range(metadata_count):
            key_len = struct.unpack(">B", file_handle.read(1))[0]
            key = file_handle.read(key_len).decode("utf-8")
            val_len = struct.unpack(">B", file_handle.read(1))[0]
            val = file_handle.read(val_len).decode("utf-8")
            metadata[key] = val

        # Read sync marker (16 bytes)
        sync_marker = file_handle.read(16)

        return {
            "version": version,
            "key_class": key_class,
            "value_class": value_class,
            "compression": compression,
            "block_compression": block_compression,
            "compression_codec": compression_codec,
            "metadata": metadata,
            "sync_marker": sync_marker,
            "header_end_position": file_handle.tell(),
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Get SequenceFile metadata.

        Returns:
            Dict: File metadata including key/value classes and compression info
        """
        if self._metadata is None:
            with self.fs_manager.open(self.file_path, "rb") as f:
                self._metadata = self._parse_header(f)

        return self._metadata

    def read_records(self, max_records: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Read records from the SequenceFile.

        This method yields records one at a time for memory-efficient processing.

        Args:
            max_records: Maximum number of records to read (None for all)

        Yields:
            Dict: Parsed record with 'key' and 'value' fields
        """
        try:
            # Parse header first to get metadata
            with self.fs_manager.open(self.file_path, "rb") as file_handle:
                metadata = self._parse_header(file_handle)
                self._metadata = metadata

            # Use hadoop library for all SequenceFiles (compressed and uncompressed)
            # The hadoop library handles all formats correctly
            if not HADOOP_AVAILABLE:
                codec_name = metadata.get('compression_codec', 'unknown') if metadata["compression"] else 'none'
                raise NotImplementedError(
                    f"SequenceFile reading requires the 'hadoop' library.\n"
                    f"File compression: {codec_name}\n"
                    f"The hadoop library is included in requirements but may not be installed.\n"
                    f"Install with: pip install -e ."
                )

            # File is closed now, so hadoop library can open it
            for record in self._read_with_hadoop_library(max_records):
                yield record
                
        except StopIteration:
            # Generator exhausted
            pass
        finally:
            # Ensure filesystem manager is closed
            if self.fs_manager:
                self.fs_manager.close()
                

    def _parse_record(
        self, key_data: bytes, value_data: bytes, key_class: str, value_class: str
    ) -> Dict[str, Any]:
        """Parse a raw record into a dictionary.

        Args:
            key_data: Raw key bytes
            value_data: Raw value bytes
            key_class: Java class name for key
            value_class: Java class name for value

        Returns:
            Dict: Parsed record
        """
        # Basic parsing - decode as text for now
        # In a full implementation, this would use proper Writable deserialization
        try:
            key_stream = BytesIO(key_data)
            value_stream = BytesIO(value_data)

            # Try to parse as Text (common for URLs)
            try:
                key = self._read_text(key_stream)
            except Exception:
                key = key_data.hex()

            # Value parsing depends on db_type
            if self.db_type == "crawldb":
                value = self._parse_crawldb_value(value_stream)
            elif self.db_type == "linkdb":
                value = self._parse_linkdb_value(value_stream)
            elif self.db_type == "hostdb":
                value = self._parse_hostdb_value(value_stream)
            else:
                # Unknown type, return raw data
                value = {"raw": value_data.hex()}

            return {"key": key, "value": value, "key_class": key_class, "value_class": value_class}

        except Exception as e:
            # If parsing fails, return raw data
            return {
                "key": key_data.hex(),
                "value": {"raw": value_data.hex(), "error": str(e)},
                "key_class": key_class,
                "value_class": value_class,
            }

    def _parse_crawldb_value(self, stream: BytesIO) -> Dict[str, Any]:
        """Parse CrawlDB value (CrawlDatum).

        Args:
            stream: Value data stream

        Returns:
            Dict: Parsed CrawlDatum fields
        """
        try:
            # CrawlDatum structure:
            # [1 byte: version]
            # [1 byte: status]
            # [8 bytes: fetch_time (long)]
            # [1 byte: retries]
            # [4 bytes: fetch_interval (int)]
            # [4 bytes: score (float)]
            # [4 bytes: signature_length (int)]
            # [N bytes: signature]
            # [metadata...]
            
            version = struct.unpack(">B", stream.read(1))[0]
            status = struct.unpack(">B", stream.read(1))[0]
            fetch_time = struct.unpack(">Q", stream.read(8))[0]
            retries = struct.unpack(">B", stream.read(1))[0]
            fetch_interval = struct.unpack(">I", stream.read(4))[0]
            score = struct.unpack(">f", stream.read(4))[0]

            return {
                "version": version,
                "status": status,
                "fetch_time": fetch_time,
                "retries": retries,
                "fetch_interval": fetch_interval,
                "score": score,
            }
        except Exception as e:
            # Return raw if parsing fails
            stream.seek(0)
            return {"raw": stream.read().hex(), "parse_error": str(e)}

    def _parse_linkdb_value(self, stream: BytesIO) -> Dict[str, Any]:
        """Parse LinkDB value (Inlinks).

        Args:
            stream: Value data stream

        Returns:
            Dict: Parsed Inlinks data
        """
        try:
            # Inlinks structure: num_inlinks (4-byte int) followed by inlink entries
            # Note: Nutch uses a regular 4-byte int here, not a vint
            num_inlinks_bytes = stream.read(4)
            if len(num_inlinks_bytes) < 4:
                return {"num_inlinks": 0, "inlinks": []}
            
            num_inlinks = struct.unpack(">I", num_inlinks_bytes)[0]
            inlinks = []

            for _ in range(num_inlinks):
                from_url = self._read_text(stream)
                anchor = self._read_text(stream)
                inlinks.append({"from_url": from_url, "anchor": anchor})

            return {"num_inlinks": num_inlinks, "inlinks": inlinks}
        except Exception as e:
            stream.seek(0)
            return {"raw": stream.read().hex(), "parse_error": str(e)}

    def _parse_hostdb_value(self, stream: BytesIO) -> Dict[str, Any]:
        """Parse HostDB value (HostDatum).

        Args:
            stream: Value data stream

        Returns:
            Dict: Parsed HostDatum fields
        """
        try:
            # HostDatum structure (simplified)
            # Read metadata count
            metadata_count = self._read_vint(stream)
            metadata = {}

            for _ in range(metadata_count):
                key = self._read_text(stream)
                value = self._read_text(stream)
                metadata[key] = value

            return {"metadata": metadata}
        except Exception:
            stream.seek(0)
            return {"raw": stream.read().hex()}

    def _read_with_hadoop_library(self, max_records: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Read SequenceFiles using the hadoop library.
        
        The hadoop library handles all SequenceFile formats correctly:
        - Uncompressed
        - Record-compressed (with various codecs)
        - Block-compressed (with various codecs)
        
        Args:
            max_records: Maximum number of records to read
            
        Yields:
            Dict: Parsed records
        """
        reader = HadoopSequenceFile.Reader(self.file_path)
        
        # Get metadata once before the loop to avoid repeated file opens
        metadata = self.get_metadata()
        
        try:
            record_count = 0
            yielded_count = 0
            
            while True:
                if max_records and yielded_count >= max_records:
                    break
                
                # Read raw (decompressed) key and value
                key_buffer = reader.nextRawKey()
                if not key_buffer:
                    # End of file
                    break
                
                value_buffer = reader.nextRawValue()
                
                # Convert to bytes
                key_data = key_buffer.toByteArray()
                value_data = value_buffer.toByteArray()
                
                # Parse key and value
                try:
                    record = self._parse_record(
                        key_data, value_data, 
                        metadata["key_class"], 
                        metadata["value_class"]
                    )
                    yield record
                    yielded_count += 1
                except Exception as e:
                    # Skip unparseable records and continue reading
                    import sys
                    print(f"Warning: Failed to parse record {record_count + 1}: {e}", file=sys.stderr)
                finally:
                    record_count += 1
                    
        finally:
            reader.close()

    def close(self) -> None:
        """Close filesystem connections."""
        if self.fs_manager:
            self.fs_manager.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
