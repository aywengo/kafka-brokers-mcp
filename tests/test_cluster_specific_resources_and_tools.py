#!/usr/bin/env python3
"""
Tests for cluster-specific MCP resources and advanced tools
Tests the cluster-specific kafka://{name} resources and advanced analysis tools.
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
    KafkaClusterManager
)
from kafka_mcp_resources import (
    get_cluster_brokers_resource,
    get_cluster_topics_resource,
    get_cluster_consumer_groups_resource,
    get_cluster_partitions_resource,
    get_cluster_health_resource
)
from kafka_mcp_tools import (
    get_partitions,
    get_cluster_health,
    compare_cluster_topics,
    get_partition_leaders,
    get_topic_partition_details,
    find_under_replicated_partitions,
    get_broker_partition_count,
    list_topics,
    list_brokers
)
import kafka_mcp_tools
import kafka_mcp_resources


class TestClusterSpecificResources:
    """Test cluster-specific MCP resources."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = KafkaClusterManager()
        
        # Initialize cluster_manager in the imported modules
        kafka_mcp_tools.set_cluster_manager(self.manager)
        kafka_mcp_resources.set_cluster_manager(self.manager)
        
        # Add test cluster
        cluster_config = KafkaClusterConfig(
            name="production",
            bootstrap_servers="localhost:9092"
        )
        self.manager.clusters = {
            "production": cluster_config
        }

    def create_mock_metadata(self, cluster_name="production"):
        """Create mock Kafka metadata for testing."""
        mock_metadata = MagicMock()
        mock_metadata.cluster_id = f"kafka-cluster-{cluster_name}"
        mock_metadata.controller_id = 1
        
        # Mock brokers
        mock_broker = MagicMock()
        mock_broker.host = f"{cluster_name}-kafka-1"
        mock_broker.port = 9092
        mock_broker.rack = "rack-1"
        mock_metadata.brokers = {1: mock_broker, 2: MagicMock(host=f"{cluster_name}-kafka-2", port=9092, rack="rack-2")}
        
        # Mock topics with partitions
        mock_topic = MagicMock()
        mock_partition1 = MagicMock()
        mock_partition1.leader = 1
        mock_partition1.replicas = [1, 2, 3]
        mock_partition1.isrs = [1, 2, 3]
        mock_partition1.error = None
        
        mock_partition2 = MagicMock()
        mock_partition2.leader = 2
        mock_partition2.replicas = [2, 1, 3]
        mock_partition2.isrs = [2, 1]  # Under-replicated
        mock_partition2.error = None
        
        mock_topic.partitions = {0: mock_partition1, 1: mock_partition2}
        mock_metadata.topics = {"user-events": mock_topic, "order-updates": mock_topic}
        
        return mock_metadata

    def create_mock_consumer_groups(self):
        """Create mock consumer groups for testing."""
        mock_group = MagicMock()
        mock_group.group_id = "analytics-service"
        mock_group.is_simple_consumer_group = False
        mock_group.state = MagicMock()
        mock_group.state.name = "STABLE"
        
        mock_result = MagicMock()
        mock_result.result.return_value = [mock_group]
        
        return mock_result

    @patch('kafka_mcp_resources.cluster_manager')
    @pytest.mark.asyncio
    async def test_get_cluster_brokers_resource(self, mock_cluster_manager):
        """Test kafka://brokers/{name} resource."""
        # Mock admin client
        mock_admin_client = MagicMock()
        mock_admin_client.list_topics.return_value = self.create_mock_metadata("production")
        mock_cluster_manager.get_admin_client.return_value = mock_admin_client
        
        result_json = await get_cluster_brokers_resource("production")
        result = json.loads(result_json)
        
        # Verify structure
        assert "cluster" in result
        assert "brokers" in result
        assert "timestamp" in result
        assert result["cluster"] == "production"
        assert isinstance(result["brokers"], list)
        assert len(result["brokers"]) == 2
        
        # Verify broker data
        broker = result["brokers"][0]
        assert "broker_id" in broker
        assert "host" in broker
        assert "port" in broker
        assert "cluster" in broker
        assert broker["cluster"] == "production"

    @patch('kafka_mcp_resources.cluster_manager')
    @pytest.mark.asyncio
    async def test_get_cluster_topics_resource(self, mock_cluster_manager):
        """Test kafka://topics/{name} resource."""
        # Mock admin client
        mock_admin_client = MagicMock()
        mock_admin_client.list_topics.return_value = self.create_mock_metadata("production")
        mock_cluster_manager.get_admin_client.return_value = mock_admin_client
        
        result_json = await get_cluster_topics_resource("production")
        result = json.loads(result_json)
        
        # Verify structure
        assert "cluster" in result
        assert "topics" in result
        assert "timestamp" in result
        assert result["cluster"] == "production"
        assert isinstance(result["topics"], list)
        assert len(result["topics"]) == 2
        
        # Verify topic data
        topic = result["topics"][0]
        assert "name" in topic
        assert "partitions" in topic
        assert "cluster" in topic
        assert topic["cluster"] == "production"

    @patch('kafka_mcp_resources.cluster_manager')
    @pytest.mark.asyncio
    async def test_get_cluster_health_resource(self, mock_cluster_manager):
        """Test kafka://cluster-health/{name} resource."""
        # Mock admin client and config
        mock_admin_client = MagicMock()
        mock_admin_client.list_topics.return_value = self.create_mock_metadata("production")
        mock_cluster_manager.get_admin_client.return_value = mock_admin_client
        
        mock_config = MagicMock()
        mock_config.bootstrap_servers = "prod-kafka:9092"
        mock_config.viewonly = True
        mock_cluster_manager.get_cluster_config.return_value = mock_config
        
        result_json = await get_cluster_health_resource("production")
        result = json.loads(result_json)
        
        # Verify structure
        assert "cluster" in result
        assert "health_status" in result
        assert "cluster_info" in result
        assert "metrics" in result
        assert "timestamp" in result
        
        # Verify health metrics
        assert result["health_status"] in ["healthy", "degraded"]
        assert "broker_count" in result["metrics"]
        assert "topic_count" in result["metrics"]
        assert "partition_count" in result["metrics"]
        assert "health_percentage" in result["metrics"]

    @patch('kafka_mcp_resources.cluster_manager')
    @pytest.mark.asyncio
    async def test_cluster_resource_error_handling(self, mock_cluster_manager):
        """Test error handling in cluster-specific resources."""
        # Mock cluster manager with error
        mock_admin_client = MagicMock()
        mock_admin_client.list_topics.side_effect = Exception("Connection failed")
        mock_cluster_manager.get_admin_client.return_value = mock_admin_client
        
        result_json = await get_cluster_brokers_resource("production")
        result = json.loads(result_json)
        
        # Should have error information
        assert "cluster" in result
        assert "error" in result
        assert "status" in result
        assert result["cluster"] == "production"
        assert result["status"] == "failed"


class TestClusterSpecificTools:
    """Test cluster-specific tools."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = KafkaClusterManager()
        
        # Initialize cluster_manager in the imported modules
        kafka_mcp_tools.set_cluster_manager(self.manager)
        kafka_mcp_resources.set_cluster_manager(self.manager)
        
        # Add test cluster
        cluster_config = KafkaClusterConfig(
            name="production",
            bootstrap_servers="localhost:9092"
        )
        self.manager.clusters = {
            "production": cluster_config
        }

    @patch('kafka_mcp_resources.get_cluster_brokers_resource')
    @pytest.mark.asyncio
    async def test_get_brokers_tool_with_cluster(self, mock_resource):
        """Test get_brokers tool with cluster parameter."""
        mock_resource.return_value = json.dumps({
            "cluster": "production",
            "brokers": [
                {"broker_id": 1, "host": "prod-kafka-1", "port": 9092, "cluster": "production"}
            ]
        })
        
        result = await list_brokers(cluster="production")
        
        assert len(result) == 1
        assert result[0]["cluster"] == "production"
        assert result[0]["broker_id"] == 1

    @patch('kafka_mcp_resources.get_cluster_topics_resource')
    @pytest.mark.asyncio
    async def test_get_topics_tool_with_cluster(self, mock_resource):
        """Test get_topics tool with cluster parameter."""
        mock_resource.return_value = json.dumps({
            "cluster": "production",
            "topics": [
                {"name": "user-events", "partitions": 6, "cluster": "production"}
            ]
        })
        
        result = await list_topics(cluster="production")
        
        assert len(result) == 1
        assert result[0]["name"] == "user-events"
        assert result[0]["cluster"] == "production"

    @patch('kafka_mcp_resources.get_cluster_partitions_resource')
    @pytest.mark.asyncio
    async def test_get_cluster_partitions_with_topic_filter(self, mock_resource):
        """Test get_cluster_partitions tool with topic filter."""
        mock_resource.return_value = json.dumps({
            "cluster": "production",
            "partitions": [
                {"topic": "user-events", "partition_id": 0, "cluster": "production"},
                {"topic": "user-events", "partition_id": 1, "cluster": "production"},
                {"topic": "order-updates", "partition_id": 0, "cluster": "production"}
            ]
        })
        
        result = await get_partitions(cluster="production", topic="user-events")
        
        # Should return only user-events partitions
        assert len(result) == 2
        for partition in result:
            assert partition["topic"] == "user-events"

    @patch('kafka_mcp_resources.get_cluster_health_resource')
    @pytest.mark.asyncio
    async def test_get_cluster_health_tool(self, mock_resource):
        """Test get_cluster_health tool."""
        mock_resource.return_value = json.dumps({
            "cluster": "production",
            "health_status": "healthy",
            "metrics": {
                "broker_count": 3,
                "topic_count": 15,
                "partition_count": 120,
                "unhealthy_partitions": 0,
                "health_percentage": 100.0
            }
        })
        
        result = await get_cluster_health("production")
        
        assert result["health_status"] == "healthy"
        assert result["metrics"]["health_percentage"] == 100.0

    @patch('kafka_brokers_unified_mcp.get_cluster_brokers_resource')
    @pytest.mark.asyncio
    async def test_cluster_tool_error_handling(self, mock_resource):
        """Test error handling in cluster tools."""
        mock_resource.return_value = json.dumps({
            "cluster": "production",
            "error": "Connection failed",
            "status": "failed"
        })
        
        with pytest.raises(ValueError, match="Failed to get brokers for cluster 'production'"):
            await list_brokers(cluster="production")


class TestAdvancedAnalysisTools:
    """Test advanced analysis and monitoring tools."""

    def setup_method(self):
        """Set up test fixtures.""" 
        self.manager = KafkaClusterManager()
        
        # Initialize cluster_manager in the imported modules
        kafka_mcp_tools.set_cluster_manager(self.manager)
        kafka_mcp_resources.set_cluster_manager(self.manager)
        
        # Add test clusters
        dev_config = KafkaClusterConfig(
            name="development",
            bootstrap_servers="localhost:9092"
        )
        prod_config = KafkaClusterConfig(
            name="production",
            bootstrap_servers="localhost:9093"
        )
        self.manager.clusters = {
            "development": dev_config,
            "production": prod_config
        }

    @patch('kafka_mcp_tools.list_topics')
    @pytest.mark.asyncio
    async def test_compare_cluster_topics(self, mock_get_topics):
        """Test compare_cluster_topics tool."""
        def mock_topics(cluster):
            if cluster == "development":
                return [
                    {"name": "user-events", "partitions": 3, "replication_factor": 2},
                    {"name": "shared-topic", "partitions": 1, "replication_factor": 1}
                ]
            else:  # production
                return [
                    {"name": "user-events", "partitions": 6, "replication_factor": 3},
                    {"name": "shared-topic", "partitions": 1, "replication_factor": 1},
                    {"name": "prod-only-topic", "partitions": 3, "replication_factor": 3}
                ]
        
        mock_get_topics.side_effect = mock_topics
        
        result = await compare_cluster_topics("development", "production")
        
        # Verify comparison structure
        assert "source_cluster" in result
        assert "target_cluster" in result
        assert "summary" in result
        assert "only_in_source" in result
        assert "only_in_target" in result
        assert "topic_differences" in result
        
        # Verify summary
        summary = result["summary"]
        assert summary["total_source_topics"] == 2
        assert summary["total_target_topics"] == 3
        assert summary["common_topics"] == 2
        assert summary["only_in_target"] == 1
        
        # Verify differences
        assert "prod-only-topic" in result["only_in_target"]
        assert len(result["topic_differences"]) == 1
        assert result["topic_differences"][0]["topic"] == "user-events"

    @patch('kafka_mcp_tools.get_partitions')
    @patch('kafka_mcp_tools.list_brokers')
    @pytest.mark.asyncio
    async def test_get_partition_leaders(self, mock_brokers, mock_partitions):
        """Test get_partition_leaders tool."""
        mock_brokers.return_value = [
            {"broker_id": 1, "host": "kafka-1", "port": 9092},
            {"broker_id": 2, "host": "kafka-2", "port": 9092}
        ]
        
        mock_partitions.return_value = [
            {"topic": "user-events", "partition_id": 0, "leader": 1},
            {"topic": "user-events", "partition_id": 1, "leader": 1},
            {"topic": "user-events", "partition_id": 2, "leader": 2},
            {"topic": "order-updates", "partition_id": 0, "leader": 2}
        ]
        
        result = await get_partition_leaders("production")
        
        # Verify structure
        assert "cluster" in result
        assert "total_partitions" in result
        assert "total_brokers" in result
        assert "leader_distribution" in result
        assert "balance_ratio" in result
        
        # Verify leader distribution
        leader_dist = result["leader_distribution"]
        assert len(leader_dist) == 2
        
        # Check broker 1 has 2 partitions as leader
        broker1_info = next(b for b in leader_dist if b["broker_id"] == 1)
        assert broker1_info["partition_count"] == 2

    @patch('kafka_mcp_tools.get_partitions')
    @pytest.mark.asyncio
    async def test_find_under_replicated_partitions(self, mock_partitions):
        """Test find_under_replicated_partitions tool."""
        mock_partitions.return_value = [
            {
                "topic": "user-events",
                "partition_id": 0,
                "leader": 1,
                "replicas": [1, 2, 3],
                "in_sync_replicas": [1, 2, 3]  # Healthy
            },
            {
                "topic": "user-events", 
                "partition_id": 1,
                "leader": 1,
                "replicas": [1, 2, 3],
                "in_sync_replicas": [1, 2]  # Under-replicated
            },
            {
                "topic": "order-updates",
                "partition_id": 0,
                "leader": 1,
                "replicas": [1, 2],
                "in_sync_replicas": [1]  # Under-replicated
            }
        ]
        
        result = await find_under_replicated_partitions("production")
        
        # Should find 2 under-replicated partitions
        assert len(result) == 2
        
        # Verify structure
        under_rep = result[0]
        assert "topic" in under_rep
        assert "partition_id" in under_rep
        assert "missing_replicas" in under_rep
        assert "replication_factor" in under_rep
        assert "cluster" in under_rep
        
        # Verify calculations
        assert under_rep["missing_replicas"] > 0

    @patch('kafka_mcp_tools.cluster_manager')
    @pytest.mark.asyncio
    async def test_get_topic_partition_details(self, mock_cluster_manager):
        """Test get_topic_partition_details tool."""
        # Mock admin client
        mock_admin_client = MagicMock()
        
        # Mock metadata for specific topic
        mock_metadata = MagicMock()
        mock_topic = MagicMock()
        
        mock_partition = MagicMock()
        mock_partition.leader = 1
        mock_partition.replicas = [1, 2, 3]
        mock_partition.isrs = [1, 2, 3]
        mock_partition.error = None
        
        mock_topic.partitions = {0: mock_partition}
        mock_metadata.topics = {"user-events": mock_topic}
        
        mock_cluster_manager.get_admin_client.return_value = mock_admin_client
        mock_cluster_manager.executor = MagicMock()
        
        # Mock the list_brokers call
        with patch('kafka_mcp_tools.list_brokers') as mock_brokers:
            mock_brokers.return_value = [
                {"broker_id": 1, "host": "kafka-1", "port": 9092},
                {"broker_id": 2, "host": "kafka-2", "port": 9092},
                {"broker_id": 3, "host": "kafka-3", "port": 9092}
            ]
            
            # Mock the executor.run_in_executor call
            async def mock_run_in_executor(executor, func):
                return mock_metadata
            
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.run_in_executor = mock_run_in_executor
                
                result = await get_topic_partition_details("production", "user-events")
                
                # Verify structure
                assert "cluster" in result
                assert "topic" in result
                assert "partition_count" in result
                assert "health" in result
                assert "partitions" in result
                
                # Verify health calculation
                assert result["health"]["healthy_partitions"] == 1
                assert result["health"]["health_percentage"] == 100.0

    @patch('kafka_mcp_tools.get_partitions')
    @patch('kafka_mcp_tools.list_brokers')
    @pytest.mark.asyncio
    async def test_get_broker_partition_count(self, mock_brokers, mock_partitions):
        """Test get_broker_partition_count tool."""
        mock_brokers.return_value = [
            {"broker_id": 1, "host": "kafka-1", "port": 9092, "rack": "rack-1"},
            {"broker_id": 2, "host": "kafka-2", "port": 9092, "rack": "rack-2"}
        ]
        
        mock_partitions.return_value = [
            {"topic": "user-events", "leader": 1, "replicas": [1, 2]},
            {"topic": "user-events", "leader": 2, "replicas": [2, 1]},
            {"topic": "order-updates", "leader": 1, "replicas": [1, 2]}
        ]
        
        result = await get_broker_partition_count("production")
        
        # Should return stats for both brokers
        assert len(result) == 2
        
        # Verify structure
        broker_stats = result[0]
        assert "broker_id" in broker_stats
        assert "host" in broker_stats
        assert "leader_count" in broker_stats
        assert "replica_count" in broker_stats
        assert "topic_count" in broker_stats
        
        # Verify counts (broker 1 should have 2 leader partitions)
        broker1_stats = next(b for b in result if b["broker_id"] == 1)
        assert broker1_stats["leader_count"] == 2
        assert broker1_stats["replica_count"] == 3  # 3 total replica assignments


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 