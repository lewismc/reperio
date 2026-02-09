"""Data readers for Apache Nutch data structures."""

from reperio.readers.database_reader import (
    NutchDatabaseReader,
    create_nutch_reader,
    discover_nutch_partitions,
)
from reperio.readers.filesystem import FileSystemManager, HDFSFileSystem, LocalFileSystem
from reperio.readers.sequencefile_reader import NutchSequenceFileReader

__all__ = [
    "FileSystemManager",
    "HDFSFileSystem",
    "LocalFileSystem",
    "NutchSequenceFileReader",
    "NutchDatabaseReader",
    "create_nutch_reader",
    "discover_nutch_partitions",
]
