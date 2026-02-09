"""Filesystem abstraction layer for local and HDFS support."""

import os
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Union
from urllib.parse import urlparse


class FileSystemManager(ABC):
    """Abstract base class for filesystem operations."""

    @abstractmethod
    def open(self, path: str, mode: str = "rb") -> BinaryIO:
        """Open a file and return a file-like object.

        Args:
            path: Path to the file
            mode: File open mode (default: 'rb')

        Returns:
            BinaryIO: File-like object
        """
        pass

    @abstractmethod
    def list_dir(self, path: str) -> List[str]:
        """List files in a directory.

        Args:
            path: Path to the directory

        Returns:
            List[str]: List of file paths
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a path exists.

        Args:
            path: Path to check

        Returns:
            bool: True if path exists
        """
        pass

    @abstractmethod
    def get_file_info(self, path: str) -> Dict:
        """Get file metadata.

        Args:
            path: Path to the file

        Returns:
            Dict: File metadata (size, modified time, etc.)
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close any open connections."""
        pass

    @staticmethod
    def create(
        path: str,
        namenode: Optional[str] = None,
        port: Optional[int] = None,
        hadoop_conf_dir: Optional[str] = None,
    ) -> "FileSystemManager":
        """Factory method to create appropriate filesystem manager.

        Args:
            path: Path to determine filesystem type
            namenode: HDFS namenode hostname (for HDFS)
            port: HDFS namenode port (for HDFS)
            hadoop_conf_dir: Path to Hadoop configuration directory

        Returns:
            FileSystemManager: Appropriate filesystem implementation
        """
        parsed = urlparse(path)
        scheme = parsed.scheme.lower() if parsed.scheme else ""

        if scheme == "hdfs":
            return HDFSFileSystem(
                namenode=namenode or parsed.netloc.split(":")[0],
                port=port or int(parsed.netloc.split(":")[1]) if ":" in parsed.netloc else 9000,
                hadoop_conf_dir=hadoop_conf_dir,
            )
        else:
            # Default to local filesystem
            return LocalFileSystem()


class LocalFileSystem(FileSystemManager):
    """Local filesystem implementation."""

    def open(self, path: str, mode: str = "rb") -> BinaryIO:
        """Open a local file.

        Args:
            path: Path to the file
            mode: File open mode

        Returns:
            BinaryIO: File object
        """
        # Handle file:// URLs
        parsed = urlparse(path)
        if parsed.scheme == "file":
            path = parsed.path

        return open(path, mode)

    def list_dir(self, path: str) -> List[str]:
        """List files in a local directory.

        Args:
            path: Path to the directory

        Returns:
            List[str]: List of file paths
        """
        parsed = urlparse(path)
        if parsed.scheme == "file":
            path = parsed.path

        path_obj = Path(path)
        if not path_obj.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        return [str(p) for p in path_obj.iterdir()]

    def exists(self, path: str) -> bool:
        """Check if a local path exists.

        Args:
            path: Path to check

        Returns:
            bool: True if path exists
        """
        parsed = urlparse(path)
        if parsed.scheme == "file":
            path = parsed.path

        return Path(path).exists()

    def get_file_info(self, path: str) -> Dict:
        """Get local file metadata.

        Args:
            path: Path to the file

        Returns:
            Dict: File metadata
        """
        parsed = urlparse(path)
        if parsed.scheme == "file":
            path = parsed.path

        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {path}")

        stat = path_obj.stat()
        return {
            "size": stat.st_size,
            "modified_time": stat.st_mtime,
            "is_dir": path_obj.is_dir(),
            "path": str(path_obj),
        }

    def close(self) -> None:
        """No-op for local filesystem."""
        pass


class HDFSFileSystem(FileSystemManager):
    """HDFS filesystem implementation using hdfs3 or pyarrow."""

    def __init__(
        self,
        namenode: str = "localhost",
        port: int = 9000,
        hadoop_conf_dir: Optional[str] = None,
    ):
        """Initialize HDFS filesystem.

        Args:
            namenode: HDFS namenode hostname
            port: HDFS namenode port
            hadoop_conf_dir: Path to Hadoop configuration directory

        Raises:
            ImportError: If neither hdfs3 nor pyarrow is available
        """
        self.namenode = namenode
        self.port = port
        self.hadoop_conf_dir = hadoop_conf_dir or os.environ.get("HADOOP_CONF_DIR")
        self._client = None

        # Try to import HDFS libraries
        self._hdfs_lib = self._initialize_hdfs_client()

    def _initialize_hdfs_client(self) -> str:
        """Initialize HDFS client using available library.

        Returns:
            str: Name of the library used ('hdfs3' or 'pyarrow')

        Raises:
            ImportError: If no HDFS library is available
        """
        # Try hdfs3 first
        try:
            import hdfs3

            self._client = hdfs3.HDFileSystem(
                host=self.namenode,
                port=self.port,
            )
            return "hdfs3"
        except ImportError:
            pass

        # Try pyarrow
        try:
            import pyarrow.fs as pafs

            self._client = pafs.HadoopFileSystem(
                host=self.namenode,
                port=self.port,
            )
            return "pyarrow"
        except ImportError:
            pass

        raise ImportError(
            "HDFS support requires either 'hdfs3' or 'pyarrow' to be installed. "
            "Install with: pip install hdfs3 or pip install pyarrow"
        )

    def _get_hdfs_path(self, path: str) -> str:
        """Extract HDFS path from URL.

        Args:
            path: Full path (may include hdfs:// prefix)

        Returns:
            str: Clean HDFS path
        """
        parsed = urlparse(path)
        if parsed.scheme == "hdfs":
            return parsed.path
        return path

    def open(self, path: str, mode: str = "rb") -> BinaryIO:
        """Open an HDFS file.

        Args:
            path: HDFS path to the file
            mode: File open mode

        Returns:
            BinaryIO: File-like object
        """
        hdfs_path = self._get_hdfs_path(path)

        if self._hdfs_lib == "hdfs3":
            return self._client.open(hdfs_path, mode)
        elif self._hdfs_lib == "pyarrow":
            # PyArrow returns a NativeFile, wrap in BytesIO for compatibility
            with self._client.open_input_file(hdfs_path) as f:
                data = f.read()
            return BytesIO(data)

        raise RuntimeError("No HDFS client initialized")

    def list_dir(self, path: str) -> List[str]:
        """List files in an HDFS directory.

        Args:
            path: HDFS path to the directory

        Returns:
            List[str]: List of file paths
        """
        hdfs_path = self._get_hdfs_path(path)

        if self._hdfs_lib == "hdfs3":
            return self._client.ls(hdfs_path)
        elif self._hdfs_lib == "pyarrow":
            file_info = self._client.get_file_info(hdfs_path)
            if file_info.type.name == "Directory":
                selector = pafs.FileSelector(hdfs_path)
                return [info.path for info in self._client.get_file_info(selector)]
            return [hdfs_path]

        raise RuntimeError("No HDFS client initialized")

    def exists(self, path: str) -> bool:
        """Check if an HDFS path exists.

        Args:
            path: HDFS path to check

        Returns:
            bool: True if path exists
        """
        hdfs_path = self._get_hdfs_path(path)

        try:
            if self._hdfs_lib == "hdfs3":
                return self._client.exists(hdfs_path)
            elif self._hdfs_lib == "pyarrow":
                file_info = self._client.get_file_info(hdfs_path)
                return file_info.type.name != "NotFound"
        except Exception:
            return False

        return False

    def get_file_info(self, path: str) -> Dict:
        """Get HDFS file metadata.

        Args:
            path: HDFS path to the file

        Returns:
            Dict: File metadata
        """
        hdfs_path = self._get_hdfs_path(path)

        if self._hdfs_lib == "hdfs3":
            info = self._client.info(hdfs_path)
            return {
                "size": info.get("size", 0),
                "modified_time": info.get("last_mod", 0),
                "is_dir": info.get("kind") == "directory",
                "path": hdfs_path,
            }
        elif self._hdfs_lib == "pyarrow":
            file_info = self._client.get_file_info(hdfs_path)
            return {
                "size": file_info.size,
                "modified_time": file_info.mtime_ns / 1e9 if file_info.mtime_ns else 0,
                "is_dir": file_info.type.name == "Directory",
                "path": hdfs_path,
            }

        raise RuntimeError("No HDFS client initialized")

    def close(self) -> None:
        """Close HDFS connection."""
        if self._client and hasattr(self._client, "close"):
            self._client.close()
