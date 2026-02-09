"""Tests for multi-partition database reader."""

import os
import tempfile
from pathlib import Path

import pytest

from reperio.readers.database_reader import discover_nutch_partitions
from reperio.readers.filesystem import LocalFileSystem


class TestPartitionDiscovery:
    """Test partition file discovery logic."""

    def test_discover_single_file(self, tmp_path):
        """Test discovery of a single partition file."""
        # Create a single data file
        partition_dir = tmp_path / "part-r-00000"
        partition_dir.mkdir()
        data_file = partition_dir / "data"
        data_file.write_text("test")
        
        fs = LocalFileSystem()
        partitions = discover_nutch_partitions(str(data_file), fs)
        
        assert len(partitions) == 1
        assert partitions[0] == str(data_file)
    
    def test_discover_multiple_partitions(self, tmp_path):
        """Test discovery of multiple partition files."""
        # Create multiple partition directories
        for i in range(3):
            partition_dir = tmp_path / f"part-r-{i:05d}"
            partition_dir.mkdir()
            data_file = partition_dir / "data"
            data_file.write_text("test")
        
        fs = LocalFileSystem()
        partitions = discover_nutch_partitions(str(tmp_path), fs)
        
        assert len(partitions) == 3
        # Check they are sorted by partition number
        assert "part-r-00000" in partitions[0]
        assert "part-r-00001" in partitions[1]
        assert "part-r-00002" in partitions[2]
    
    def test_discover_with_current_directory(self, tmp_path):
        """Test discovery when pointing to database root with current/ subdirectory."""
        # Create database structure with current directory
        current_dir = tmp_path / "current"
        current_dir.mkdir()
        
        for i in range(2):
            partition_dir = current_dir / f"part-r-{i:05d}"
            partition_dir.mkdir()
            data_file = partition_dir / "data"
            data_file.write_text("test")
        
        fs = LocalFileSystem()
        # Point to database root, not current
        partitions = discover_nutch_partitions(str(tmp_path), fs)
        
        assert len(partitions) == 2
        assert "current" in partitions[0]
        assert "current" in partitions[1]
    
    def test_discover_mixed_partition_names(self, tmp_path):
        """Test discovery with different partition naming patterns."""
        # Create partitions with and without 'r' in name
        partition_dir1 = tmp_path / "part-r-00000"
        partition_dir1.mkdir()
        (partition_dir1 / "data").write_text("test")
        
        partition_dir2 = tmp_path / "part-00001"
        partition_dir2.mkdir()
        (partition_dir2 / "data").write_text("test")
        
        fs = LocalFileSystem()
        partitions = discover_nutch_partitions(str(tmp_path), fs)
        
        assert len(partitions) == 2
    
    def test_discover_ignores_non_partition_dirs(self, tmp_path):
        """Test that discovery ignores non-partition directories."""
        # Create some partition directories
        for i in range(2):
            partition_dir = tmp_path / f"part-r-{i:05d}"
            partition_dir.mkdir()
            (partition_dir / "data").write_text("test")
        
        # Create some non-partition directories
        (tmp_path / "some-other-dir").mkdir()
        (tmp_path / "logs").mkdir()
        
        fs = LocalFileSystem()
        partitions = discover_nutch_partitions(str(tmp_path), fs)
        
        # Should only find the partition directories
        assert len(partitions) == 2
    
    def test_discover_no_partitions_raises_error(self, tmp_path):
        """Test that discovery raises error when no partitions found."""
        # Create empty directory
        fs = LocalFileSystem()
        
        with pytest.raises(ValueError, match="No Nutch partition files found"):
            discover_nutch_partitions(str(tmp_path), fs)
    
    def test_discover_nonexistent_path_raises_error(self, tmp_path):
        """Test that discovery raises error for nonexistent path."""
        fs = LocalFileSystem()
        nonexistent = tmp_path / "does-not-exist"
        
        with pytest.raises(FileNotFoundError):
            discover_nutch_partitions(str(nonexistent), fs)
    
    def test_discover_sorts_partitions_numerically(self, tmp_path):
        """Test that partitions are sorted by number, not lexicographically."""
        # Create partitions out of order
        for i in [10, 2, 1, 20, 5]:
            partition_dir = tmp_path / f"part-r-{i:05d}"
            partition_dir.mkdir()
            (partition_dir / "data").write_text("test")
        
        fs = LocalFileSystem()
        partitions = discover_nutch_partitions(str(tmp_path), fs)
        
        assert len(partitions) == 5
        # Should be in numerical order
        assert "part-r-00001" in partitions[0]
        assert "part-r-00002" in partitions[1]
        assert "part-r-00005" in partitions[2]
        assert "part-r-00010" in partitions[3]
        assert "part-r-00020" in partitions[4]


class TestNutchDatabaseReader:
    """Test multi-partition database reader."""
    
    def test_reader_accepts_progress_callback(self):
        """Test that reader accepts and stores progress callback."""
        from reperio.readers.database_reader import NutchDatabaseReader
        from reperio.readers.filesystem import LocalFileSystem
        
        callback_called = []
        
        def callback(partition_num, total_partitions, path):
            callback_called.append((partition_num, total_partitions, path))
        
        fs = LocalFileSystem()
        reader = NutchDatabaseReader(
            partition_files=["/path/to/part-r-00000/data"],
            db_type="crawldb",
            fs_manager=fs,
            progress_callback=callback,
        )
        
        assert reader.progress_callback == callback
    
    def test_get_partition_count(self):
        """Test getting partition count."""
        from reperio.readers.database_reader import NutchDatabaseReader
        from reperio.readers.filesystem import LocalFileSystem
        
        fs = LocalFileSystem()
        reader = NutchDatabaseReader(
            partition_files=[
                "/path/to/part-r-00000/data",
                "/path/to/part-r-00001/data",
                "/path/to/part-r-00002/data",
            ],
            db_type="crawldb",
            fs_manager=fs,
        )
        
        assert reader.get_partition_count() == 3
    
    def test_get_partition_files(self):
        """Test getting partition file list."""
        from reperio.readers.database_reader import NutchDatabaseReader
        from reperio.readers.filesystem import LocalFileSystem
        
        fs = LocalFileSystem()
        partition_files = [
            "/path/to/part-r-00000/data",
            "/path/to/part-r-00001/data",
        ]
        reader = NutchDatabaseReader(
            partition_files=partition_files,
            db_type="crawldb",
            fs_manager=fs,
        )
        
        # Should return a copy, not the original list
        result = reader.get_partition_files()
        assert result == partition_files
        assert result is not partition_files
