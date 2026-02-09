"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from reperio.api.main import app


client = TestClient(app)


class TestAPIEndpoints:
    """Test API endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_get_hdfs_config(self):
        """Test getting HDFS configuration."""
        response = client.get("/api/config/hdfs")
        assert response.status_code == 200
        data = response.json()
        assert "namenode" in data
        assert "port" in data

    def test_get_graph_summary_no_data(self):
        """Test getting summary when no graph is loaded."""
        response = client.get("/api/graph/summary")
        assert response.status_code == 404

    def test_get_nodes_no_data(self):
        """Test getting nodes when no graph is loaded."""
        response = client.get("/api/graph/nodes")
        assert response.status_code == 404

    def test_search_no_data(self):
        """Test search when no graph is loaded."""
        response = client.get("/api/search?q=test")
        assert response.status_code == 404

    def test_load_graph_invalid_type(self):
        """Test loading graph with invalid db_type."""
        response = client.post(
            "/api/graph/load",
            json={
                "path": "/nonexistent/path",
                "db_type": "invalid_type",
                "storage": "local",
            },
        )
        assert response.status_code in [400, 500]
