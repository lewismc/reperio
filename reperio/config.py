"""Configuration management for Reperio."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration."""

    # HDFS settings
    hdfs_namenode: str = Field(
        default="localhost", description="HDFS namenode hostname", env="HDFS_NAMENODE"
    )
    hdfs_port: int = Field(default=9000, description="HDFS namenode port", env="HDFS_PORT")
    hadoop_conf_dir: Optional[str] = Field(
        default=None, description="Path to Hadoop configuration directory", env="HADOOP_CONF_DIR"
    )

    # API settings
    api_host: str = Field(default="0.0.0.0", description="API server host", env="API_HOST")
    api_port: int = Field(default=8000, description="API server port", env="API_PORT")
    api_reload: bool = Field(
        default=False, description="Enable auto-reload for development", env="API_RELOAD"
    )

    # CORS settings
    cors_origins: list = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )

    # Cache settings
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".reperio" / "cache",
        description="Cache directory for processed graphs",
    )
    cache_enabled: bool = Field(default=True, description="Enable caching", env="CACHE_ENABLED")

    # Graph processing settings
    default_max_nodes: int = Field(
        default=10000, description="Default maximum nodes for visualization"
    )
    default_sample_method: str = Field(
        default="pagerank", description="Default sampling method (random, pagerank, degree)"
    )

    # Visualization settings
    layout_algorithm: str = Field(
        default="spring", description="Default graph layout algorithm"
    )
    layout_iterations: int = Field(default=50, description="Number of layout iterations")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get configuration instance.

    Returns:
        Config: Configuration object
    """
    return config
