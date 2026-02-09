"""Multi-partition database reader for Apache Nutch data structures."""

import os
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from reperio.readers.filesystem import FileSystemManager
from reperio.readers.sequencefile_reader import NutchSequenceFileReader


class NutchDatabaseReader:
    """Reader that aggregates multiple SequenceFile partitions.
    
    This reader discovers and reads all partition files (part-r-*) in a
    Nutch database directory, providing a unified interface to read records
    from all partitions sequentially.
    """

    def __init__(
        self,
        partition_files: List[str],
        db_type: str,
        fs_manager: FileSystemManager,
        progress_callback: Optional[callable] = None,
    ):
        """Initialize multi-partition database reader.
        
        Args:
            partition_files: List of partition file paths (sorted)
            db_type: Type of Nutch database (crawldb, linkdb, hostdb)
            fs_manager: Filesystem manager for file operations
            progress_callback: Optional callback function called for each partition
                             with (partition_num, total_partitions, partition_path)
        """
        self.partition_files = partition_files
        self.db_type = db_type.lower()
        self.fs_manager = fs_manager
        self.progress_callback = progress_callback
        self._readers: List[NutchSequenceFileReader] = []
        
    def read_records(
        self,
        max_records: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Read records from all partitions sequentially.
        
        Args:
            max_records: Maximum total records to read (None for all)
            progress_callback: Optional callback function called for each partition
                             with (partition_num, total_partitions, partition_path).
                             If not provided, uses the callback from __init__.
        
        Yields:
            Dict: Record from SequenceFile with 'key' and 'value' fields
        """
        # Use provided callback or fall back to instance callback
        callback = progress_callback or self.progress_callback
        
        total_read = 0
        total_partitions = len(self.partition_files)
        
        for partition_num, partition_file in enumerate(self.partition_files, start=1):
            # Notify progress if callback provided
            if callback:
                callback(partition_num, total_partitions, partition_file)
            
            # Create reader for this partition
            reader = NutchSequenceFileReader(
                file_path=partition_file,
                db_type=self.db_type,
                fs_manager=self.fs_manager,
            )
            
            # Read records from this partition
            remaining = None if max_records is None else max_records - total_read
            
            for record in reader.read_records(max_records=remaining):
                yield record
                total_read += 1
                
                # Check if we've hit the limit
                if max_records and total_read >= max_records:
                    return
    
    def get_partition_count(self) -> int:
        """Get the number of partition files.
        
        Returns:
            int: Number of partition files
        """
        return len(self.partition_files)
    
    def get_partition_files(self) -> List[str]:
        """Get the list of partition file paths.
        
        Returns:
            List[str]: List of partition file paths
        """
        return self.partition_files.copy()


def discover_nutch_partitions(
    path: str,
    fs_manager: FileSystemManager,
) -> List[str]:
    """Discover all partition files in a Nutch database directory.
    
    This function handles several Nutch directory structures:
    1. Direct partition file: /path/to/part-r-00000/data
    2. Current directory: /path/to/crawldb/current/
    3. Database root: /path/to/crawldb/ (will look for 'current' subdirectory)
    
    Args:
        path: Path to Nutch database (file or directory)
        fs_manager: Filesystem manager for file operations
    
    Returns:
        List[str]: Sorted list of partition file paths
    
    Raises:
        FileNotFoundError: If path doesn't exist
        ValueError: If no partition files found
    """
    if not fs_manager.exists(path):
        raise FileNotFoundError(f"Path not found: {path}")
    
    file_info = fs_manager.get_file_info(path)
    
    # Case 1: Path is a file (single partition)
    if not file_info.get('is_dir', False):
        # Check if it's a 'data' file inside a partition directory
        if os.path.basename(path) == 'data':
            return [path]
        # Otherwise, treat it as a SequenceFile directly
        return [path]
    
    # Case 2: Path is a directory
    # Check if it contains 'current' subdirectory (Nutch database root)
    current_path = os.path.join(path, 'current')
    if fs_manager.exists(current_path):
        file_info = fs_manager.get_file_info(current_path)
        if file_info.get('is_dir', False):
            path = current_path
    
    # Find all partition directories
    partition_files = []
    
    try:
        dir_contents = fs_manager.list_dir(path)
    except Exception as e:
        raise ValueError(f"Failed to list directory {path}: {e}")
    
    # Pattern matches: part-r-00000, part-00000, part-r-0, etc.
    partition_pattern = re.compile(r'^part-r?-(\d+)$')
    
    for item in dir_contents:
        item_name = os.path.basename(item.rstrip('/'))
        match = partition_pattern.match(item_name)
        
        if match:
            partition_num = int(match.group(1))
            
            # Check for 'data' file inside partition directory
            data_file = os.path.join(item, 'data')
            
            if fs_manager.exists(data_file):
                partition_files.append((partition_num, data_file))
            # Also check if the partition directory itself is a file (some Nutch versions)
            elif not fs_manager.get_file_info(item).get('is_dir', True):
                partition_files.append((partition_num, item))
    
    if not partition_files:
        raise ValueError(
            f"No Nutch partition files found in {path}. "
            f"Expected directories matching pattern 'part-r-NNNNN' or 'part-NNNNN' "
            f"containing 'data' files."
        )
    
    # Sort by partition number and return just the paths
    partition_files.sort(key=lambda x: x[0])
    return [path for _, path in partition_files]


def create_nutch_reader(
    path: str,
    db_type: str,
    fs_manager: FileSystemManager,
    progress_callback: Optional[callable] = None,
):
    """Factory function to create appropriate reader for single or multi-partition data.
    
    Args:
        path: Path to Nutch data (file or directory)
        db_type: Type of Nutch database (crawldb, linkdb, hostdb)
        fs_manager: Filesystem manager
        progress_callback: Optional callback for multi-partition progress reporting
    
    Returns:
        NutchSequenceFileReader or NutchDatabaseReader: Appropriate reader instance
    """
    partition_files = discover_nutch_partitions(path, fs_manager)
    
    if len(partition_files) == 1:
        # Single partition - use simple reader
        return NutchSequenceFileReader(
            file_path=partition_files[0],
            db_type=db_type,
            fs_manager=fs_manager,
        )
    else:
        # Multiple partitions - use aggregating reader
        return NutchDatabaseReader(
            partition_files=partition_files,
            db_type=db_type,
            fs_manager=fs_manager,
            progress_callback=progress_callback,
        )
