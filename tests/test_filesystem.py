"""Tests for filesystem abstraction layer."""

import tempfile
from pathlib import Path

import pytest

from reperio.readers.filesystem import FileSystemManager, LocalFileSystem


class TestLocalFileSystem:
    """Test local filesystem operations."""

    def test_create_local_filesystem(self):
        """Test creating local filesystem manager."""
        fs = FileSystemManager.create("/tmp/test")
        assert isinstance(fs, LocalFileSystem)

    def test_create_with_file_scheme(self):
        """Test creating with file:// scheme."""
        fs = FileSystemManager.create("file:///tmp/test")
        assert isinstance(fs, LocalFileSystem)

    def test_file_exists(self):
        """Test checking file existence."""
        fs = LocalFileSystem()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"test data")
        
        try:
            assert fs.exists(str(tmp_path))
            assert not fs.exists("/nonexistent/path")
        finally:
            tmp_path.unlink()

    def test_list_directory(self):
        """Test listing directory contents."""
        fs = LocalFileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            (Path(tmpdir) / "file1.txt").write_text("test1")
            (Path(tmpdir) / "file2.txt").write_text("test2")
            
            files = fs.list_dir(tmpdir)
            assert len(files) == 2
            assert any("file1.txt" in f for f in files)
            assert any("file2.txt" in f for f in files)

    def test_get_file_info(self):
        """Test getting file metadata."""
        fs = LocalFileSystem()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"test data")
        
        try:
            info = fs.get_file_info(str(tmp_path))
            assert info["size"] == 9
            assert "modified_time" in info
            assert info["is_dir"] is False
        finally:
            tmp_path.unlink()

    def test_open_file(self):
        """Test opening and reading files."""
        fs = LocalFileSystem()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"test data")
        
        try:
            with fs.open(str(tmp_path), "rb") as f:
                content = f.read()
                assert content == b"test data"
        finally:
            tmp_path.unlink()

    def test_close(self):
        """Test closing filesystem."""
        fs = LocalFileSystem()
        fs.close()  # Should not raise


class TestHDFSFileSystem:
    """Test HDFS filesystem operations (requires HDFS libraries)."""

    def test_hdfs_creation_requires_libraries(self):
        """Test that HDFS creation fails without required libraries."""
        with pytest.raises(ImportError):
            fs = FileSystemManager.create("hdfs://localhost:9000/test")
