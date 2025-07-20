#!/usr/bin/env python3
"""
Tests for new MCP resources and tools
Tests the new kafka:// resources and corresponding get_ tools added in the latest version.
"""

import asyncio
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, List, Any

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from kafka_cluster_manager import (
    KafkaClusterConfig,
    KafkaClusterManager,
    load_cluster_configurations
)
from kafka_mcp_resources import (
    get_brokers_resource,
    get_topics_resource,
    get_consumer_groups_resource,
    get_partitions_resource
)
from kafka_mcp_tools import (
    get_partitions,
    list_topics,
    list_brokers,
    list_consumer_groups
)
import kafka_mcp_tools
import kafka_mcp_resources


class TestNewResources:
    """Test the new MCP resources."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = KafkaClusterManager()
        
        # Initialize cluster_manager in the imported modules
        kafka_mcp_tools.set_cluster_manager(self.manager)
        kafka_mcp_resources.set_cluster_manager(self.manager)
        
        # Add test clusters
        self.manager.add_cluster(KafkaClusterConfig(
            name="test-cluster-1",
            bootstrap_servers="localhost:9092",
            viewonly=False
        ))
        
        self.manager.add_cluster(KafkaClusterConfig(
            name="test-cluster-2", 
            bootstrap_servers="localhost:9093",
            viewonly=True
        ))

    def create_mock_metadata(self, cluster_name="test-cluster-1"):
        """Create mock Kafka metadata for testing."""
        mock_metadata = MagicMock()
        
        # Mock brokers
        mock_broker = MagicMock()
        mock_broker.host = "localhost"
        mock_broker.port = 9092
        mock_broker.rack = None
        mock_metadata.brokers = {1: mock_broker}
        
        # Mock topics with partitions
        mock_topic = MagicMock()
        mock_partition = MagicMock()
        mock_partition.leader = 1
        mock_partition.replicas = [1, 2, 3]
        mock_partition.isrs = [1, 2, 3]
        mock_partition.error = None
        mock_topic.partitions = {0: mock_partition, 1: mock_partition}
        mock_metadata.topics = {"test-topic": mock_topic}
        
        return mock_metadata

    def create_mock_consumer_groups(self):
        """Create mock consumer groups for testing."""
        mock_group = MagicMock()
        mock_group.group_id = "test-consumer-group"
        mock_group.is_simple_consumer_group = False
        mock_group.state = MagicMock()
        mock_group.state.name = "STABLE"
        
        mock_result = MagicMock()
        mock_result.result.return_value = [mock_group]
        
        return mock_result

    @patch('kafka_mcp_resources.cluster_manager')
    @pytest.mark.asyncio
    async def test_get_brokers_resource(self, mock_cluster_manager):
        """Test kafka://brokers resource."""
        # Mock the cluster manager - mock clusters as MagicMock so .keys() is mockable
        mock_clusters = MagicMock()
        mock_clusters.keys.return_value = ["test-cluster-1", "test-cluster-2"]
        mock_cluster_manager.clusters = mock_clusters
        
        # Mock admin clients
        mock_admin_client = MagicMock()
        mock_admin_client.list_topics.return_value = self.create_mock_metadata()
        mock_cluster_manager.get_admin_client.return_value = mock_admin_client
        
        # Test the resource
        result_json = await get_brokers_resource()
        result = json.loads(result_json)
        
        # Verify structure
        assert "brokers" in result
        assert "timestamp" in result
        assert isinstance(result["brokers"], dict)
        
        # Verify broker data for each cluster
        for cluster_name in ["test-cluster-1", "test-cluster-2"]:
            if cluster_name in result["brokers"] and isinstance(result["brokers"][cluster_name], list):
                broker = result["brokers"][cluster_name][0]
                assert "broker_id" in broker
                assert "host" in broker
                assert "port" in broker
                assert "cluster" in broker
                assert broker["cluster"] == cluster_name

    @patch('kafka_mcp_resources.cluster_manager')
    @pytest.mark.asyncio
    async def test_get_topics_resource(self, mock_cluster_manager):
        """Test kafka://topics resource."""
        # Mock the cluster manager - mock clusters as MagicMock so .keys() is mockable
        mock_clusters = MagicMock()
        mock_clusters.keys.return_value = ["test-cluster-1"]
        mock_cluster_manager.clusters = mock_clusters
        
        # Mock admin client
        mock_admin_client = MagicMock()
        mock_admin_client.list_topics.return_value = self.create_mock_metadata()
        mock_cluster_manager.get_admin_client.return_value = mock_admin_client
        
        # Test the resource
        result_json = await get_topics_resource()
        result = json.loads(result_json)
        
        # Verify structure
        assert "topics" in result
        assert "timestamp" in result
        assert isinstance(result["topics"], dict)
        
        # Verify topic data
        if "test-cluster-1" in result["topics"] and isinstance(result["topics"]["test-cluster-1"], list):
            topic = result["topics"]["test-cluster-1"][0]
            assert "name" in topic
            assert "partitions" in topic
            assert "replication_factor" in topic
            assert "cluster" in topic
            assert topic["cluster"] == "test-cluster-1"

    @patch('kafka_mcp_resources.cluster_manager')
    @pytest.mark.asyncio
    async def test_get_consumer_groups_resource(self, mock_cluster_manager):
        """Test kafka://consumer-groups resource."""
        # Mock the cluster manager - mock clusters as MagicMock so .keys() is mockable
        mock_clusters = MagicMock()
        mock_clusters.keys.return_value = ["test-cluster-1"]
        mock_cluster_manager.clusters = mock_clusters
        
        # Mock admin client
        mock_admin_client = MagicMock()
        mock_admin_client.list_consumer_groups.return_value = self.create_mock_consumer_groups()
        mock_cluster_manager.get_admin_client.return_value = mock_admin_client
        
        # Test the resource
        result_json = await get_consumer_groups_resource()
        result = json.loads(result_json)
        
        # Verify structure
        assert "consumer_groups" in result
        assert "timestamp" in result
        assert isinstance(result["consumer_groups"], dict)

    @patch('kafka_mcp_resources.cluster_manager')
    @pytest.mark.asyncio
    async def test_get_partitions_resource(self, mock_cluster_manager):
        """Test kafka://partitions resource."""
        # Mock the cluster manager - mock clusters as MagicMock so .keys() is mockable
        mock_clusters = MagicMock()
        mock_clusters.keys.return_value = ["test-cluster-1"]
        mock_cluster_manager.clusters = mock_clusters
        
        # Mock admin client
        mock_admin_client = MagicMock()
        mock_admin_client.list_topics.return_value = self.create_mock_metadata()
        mock_cluster_manager.get_admin_client.return_value = mock_admin_client
        
        # Test the resource
        result_json = await get_partitions_resource()
        result = json.loads(result_json)
        
        # Verify structure
        assert "partitions" in result
        assert "timestamp" in result
        assert isinstance(result["partitions"], dict)
        
        # Verify partition data
        if "test-cluster-1" in result["partitions"] and isinstance(result["partitions"]["test-cluster-1"], list):
            partition = result["partitions"]["test-cluster-1"][0]
            assert "topic" in partition
            assert "partition_id" in partition
            assert "leader" in partition
            assert "replicas" in partition
            assert "cluster" in partition
            assert partition["cluster"] == "test-cluster-1"


class TestNewTools:
    """Test the new MCP tools that use resources."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = KafkaClusterManager()
        
        # Initialize cluster_manager in the imported modules
        kafka_mcp_tools.set_cluster_manager(self.manager)
        kafka_mcp_resources.set_cluster_manager(self.manager)
        
        # Add test clusters
        cluster1_config = KafkaClusterConfig(
            name="cluster1",
            bootstrap_servers="localhost:9092"
        )
        cluster2_config = KafkaClusterConfig(
            name="cluster2", 
            bootstrap_servers="localhost:9093"
        )
        self.manager.clusters = {
            "cluster1": cluster1_config,
            "cluster2": cluster2_config
        }

    @patch('kafka_mcp_resources.get_brokers_resource')
    @pytest.mark.asyncio
    async def test_get_brokers_tool_all_clusters(self, mock_resource):
        """Test get_brokers tool without cluster filter."""
        # Mock resource response
        mock_resource.return_value = json.dumps({
            "brokers": {
                "cluster1": [
                    {"broker_id": 1, "host": "host1", "port": 9092, "cluster": "cluster1"}
                ],
                "cluster2": [
                    {"broker_id": 2, "host": "host2", "port": 9092, "cluster": "cluster2"}
                ]
            }
        })
        
        result = await list_brokers()
        
        # Should return brokers from all clusters
        assert len(result) == 2
        assert result[0]["cluster"] in ["cluster1", "cluster2"]
        assert result[1]["cluster"] in ["cluster1", "cluster2"]

    @patch('kafka_mcp_resources.get_cluster_brokers_resource')
    @pytest.mark.asyncio
    async def test_get_brokers_tool_specific_cluster(self, mock_cluster_resource):
        """Test get_brokers tool with cluster filter."""
        # Mock cluster-specific resource response
        mock_cluster_resource.return_value = json.dumps({
            "cluster": "cluster1",
            "brokers": [
                {"broker_id": 1, "host": "host1", "port": 9092, "cluster": "cluster1"}
            ]
        })
        
        result = await list_brokers(cluster="cluster1")
        
        # Should return only brokers from cluster1
        assert len(result) == 1
        assert result[0]["cluster"] == "cluster1"

    @patch('kafka_mcp_resources.get_topics_resource')
    @pytest.mark.asyncio
    async def test_get_topics_tool_all_clusters(self, mock_resource):
        """Test get_topics tool without cluster filter."""
        # Mock resource response
        mock_resource.return_value = json.dumps({
            "topics": {
                "cluster1": [
                    {"name": "topic1", "partitions": 3, "cluster": "cluster1"}
                ],
                "cluster2": [
                    {"name": "topic2", "partitions": 6, "cluster": "cluster2"}
                ]
            }
        })
        
        result = await list_topics()
        
        # Should return topics from all clusters, sorted by name
        assert len(result) == 2
        assert result[0]["name"] in ["topic1", "topic2"]
        assert result[1]["name"] in ["topic1", "topic2"]

    @patch('kafka_mcp_resources.get_cluster_consumer_groups_resource')
    @pytest.mark.asyncio
    async def test_get_consumer_groups_tool_specific_cluster(self, mock_cluster_resource):
        """Test get_consumer_groups tool with cluster filter."""
        # Mock cluster-specific resource response
        mock_cluster_resource.return_value = json.dumps({
            "cluster": "cluster2",
            "consumer_groups": [
                {"group_id": "group2", "state": "STABLE", "cluster": "cluster2"}
            ]
        })
        
        result = await list_consumer_groups(cluster="cluster2")
        
        # Should return only groups from cluster2
        assert len(result) == 1
        assert result[0]["cluster"] == "cluster2"
        assert result[0]["group_id"] == "group2"

    @patch('kafka_mcp_resources.get_partitions_resource')
    @pytest.mark.asyncio
    async def test_get_partitions_tool_with_topic_filter(self, mock_resource):
        """Test get_partitions tool with topic filter."""
        # Mock resource response
        mock_resource.return_value = json.dumps({
            "partitions": {
                "cluster1": [
                    {"topic": "topic1", "partition_id": 0, "cluster": "cluster1"},
                    {"topic": "topic1", "partition_id": 1, "cluster": "cluster1"},
                    {"topic": "topic2", "partition_id": 0, "cluster": "cluster1"}
                ]
            }
        })
        
        result = await get_partitions(topic="topic1")
        
        # Should return only partitions for topic1
        assert len(result) == 2
        for partition in result:
            assert partition["topic"] == "topic1"

    @patch('kafka_mcp_resources.get_cluster_partitions_resource')
    @pytest.mark.asyncio
    async def test_get_partitions_tool_with_cluster_and_topic_filter(self, mock_cluster_resource):
        """Test get_partitions tool with both cluster and topic filters."""
        # Mock cluster-specific resource response
        mock_cluster_resource.return_value = json.dumps({
            "cluster": "cluster1",
            "partitions": [
                {"topic": "topic1", "partition_id": 0, "cluster": "cluster1"},
                {"topic": "topic2", "partition_id": 0, "cluster": "cluster1"}
            ]
        })
        
        result = await get_partitions(cluster="cluster1", topic="topic1")
        
        # Should return only partitions for topic1 in cluster1
        assert len(result) == 1
        assert result[0]["topic"] == "topic1"
        assert result[0]["cluster"] == "cluster1"

    @patch('kafka_mcp_resources.get_brokers_resource')
    @pytest.mark.asyncio
    async def test_get_brokers_tool_nonexistent_cluster(self, mock_resource):
        """Test get_brokers tool with nonexistent cluster."""
        # Mock resource response
        mock_resource.return_value = json.dumps({
            "brokers": {
                "cluster1": [
                    {"broker_id": 1, "host": "host1", "port": 9092, "cluster": "cluster1"}
                ]
            }
        })
        
        with pytest.raises(ValueError, match="Cluster 'nonexistent' not found"):
            await list_brokers(cluster="nonexistent")

    @patch('kafka_mcp_resources.get_brokers_resource')
    @pytest.mark.asyncio
    async def test_tools_handle_error_responses(self, mock_resource):
        """Test that tools handle error responses from resources."""
        # Mock resource response with error
        mock_resource.return_value = json.dumps({
            "brokers": {
                "cluster1": {
                    "error": "Connection failed",
                    "status": "failed"
                }
            }
        })
        
        result = await list_brokers()
        
        # Should return empty list when all clusters have errors
        assert len(result) == 0


class TestResourceErrorHandling:
    """Test error handling in resources."""

    @patch('kafka_mcp_resources.cluster_manager')
    @pytest.mark.asyncio
    async def test_brokers_resource_connection_error(self, mock_cluster_manager):
        """Test kafka://brokers resource handles connection errors."""
        # Mock cluster manager with error - mock clusters as MagicMock so .keys() is mockable
        mock_clusters = MagicMock()
        mock_clusters.keys.return_value = ["test-cluster"]
        mock_cluster_manager.clusters = mock_clusters
        mock_admin_client = MagicMock()
        mock_admin_client.list_topics.side_effect = Exception("Connection failed")
        mock_cluster_manager.get_admin_client.return_value = mock_admin_client
        
        result_json = await get_brokers_resource()
        result = json.loads(result_json)
        
        # Should have error information
        assert "brokers" in result
        assert "test-cluster" in result["brokers"]
        assert "error" in result["brokers"]["test-cluster"]
        assert "status" in result["brokers"]["test-cluster"]
        assert result["brokers"]["test-cluster"]["status"] == "failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 