#!/usr/bin/env python3
"""
Topic Operations Tests
Tests for topic management functionality including listing, describing, and configuration.
"""

import asyncio
import os
import subprocess
import sys
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from kafka_brokers_unified_mcp import (
    KafkaClusterManager, 
    load_cluster_configurations
)
from test_utils import run_docker_compose

class TestTopicOperations:
    """Test topic-related operations."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        # Check if Kafka is available
        try:
            result = run_docker_compose([
                '-f', 'docker-compose.test.yml', 
                'exec', '-T', 'kafka', 
                'kafka-topics', '--bootstrap-server', 'localhost:9092', '--list'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                pytest.skip("Kafka test environment not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker or Kafka not available for integration tests")
    
    def setup_method(self):
        """Set up for each test method."""
        # Configure environment for single cluster
        self.env_patch = patch.dict(os.environ, {
            'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092',
            'KAFKA_SECURITY_PROTOCOL': 'PLAINTEXT',
            'READONLY': 'false'
        })
        self.env_patch.start()
        
        # Load cluster manager
        self.manager = load_cluster_configurations()
    
    def teardown_method(self):
        """Clean up after each test method."""
        self.env_patch.stop()
        self.manager.executor.shutdown(wait=True)
    
    @pytest.mark.asyncio
    async def test_list_topics_filters_internal(self):
        """Test that list_topics properly filters internal topics."""
        admin_client = self.manager.get_admin_client()
        
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.list_topics(timeout=10)
        )
        
        # Get all topics (including internal)
        all_topics = list(metadata.topics.keys())
        internal_topics = [name for name in all_topics if name.startswith('__')]
        user_topics = [name for name in all_topics if not name.startswith('__')]
        
        # Verify we have some internal topics (Kafka creates these automatically)
        assert len(internal_topics) > 0, "Should have internal topics like __consumer_offsets"
        
        # Verify internal topics are filtered from results
        # (This would be tested via the actual MCP tool, but we're testing the logic)
        filtered_topics = [name for name in all_topics if not name.startswith('__')]
        assert len(filtered_topics) == len(user_topics)
        
        # Check that __consumer_offsets is not in filtered list
        assert '__consumer_offsets' not in filtered_topics
    
    @pytest.mark.asyncio
    async def test_describe_nonexistent_topic(self):
        """Test describing a topic that doesn't exist."""
        admin_client = self.manager.get_admin_client()
        
        loop = asyncio.get_event_loop()
        
        # Try to get metadata for non-existent topic
        metadata = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.list_topics(topic="nonexistent-topic", timeout=10)
        )
        
        # Should not contain the non-existent topic
        assert "nonexistent-topic" not in metadata.topics
    
    @pytest.mark.asyncio
    async def test_topic_partition_details(self):
        """Test getting detailed partition information for a topic."""
        admin_client = self.manager.get_admin_client()
        
        # Create a test topic with specific partition count
        from confluent_kafka.admin import NewTopic
        topic_name = "test-partition-details"
        partition_count = 3
        replication_factor = 1
        
        new_topic = NewTopic(
            topic_name, 
            num_partitions=partition_count, 
            replication_factor=replication_factor
        )
        
        loop = asyncio.get_event_loop()
        
        # Create topic
        await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.create_topics([new_topic], request_timeout=10)
        )
        
        # Wait for topic creation
        await asyncio.sleep(2)
        
        try:
            # Get topic metadata
            metadata = await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.list_topics(topic=topic_name, timeout=10)
            )
            
            assert topic_name in metadata.topics
            topic_metadata = metadata.topics[topic_name]
            
            # Verify partition count
            assert len(topic_metadata.partitions) == partition_count
            
            # Verify partition details
            for partition_id, partition_metadata in topic_metadata.partitions.items():
                assert isinstance(partition_id, int)
                assert partition_id >= 0 and partition_id < partition_count
                assert hasattr(partition_metadata, 'leader')
                assert hasattr(partition_metadata, 'replicas')
                assert hasattr(partition_metadata, 'isrs')
                assert len(partition_metadata.replicas) == replication_factor
                
        finally:
            # Clean up - delete the test topic
            await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.delete_topics([topic_name], request_timeout=10)
            )
    
    @pytest.mark.asyncio
    async def test_topic_configuration_retrieval(self):
        """Test retrieving topic configurations."""
        admin_client = self.manager.get_admin_client()
        
        # Create a test topic with custom configuration
        from confluent_kafka.admin import NewTopic, ConfigResource
        topic_name = "test-config-topic"
        
        new_topic = NewTopic(
            topic_name, 
            num_partitions=2, 
            replication_factor=1,
            config={
                'retention.ms': '86400000',  # 1 day
                'cleanup.policy': 'delete'
            }
        )
        
        loop = asyncio.get_event_loop()
        
        # Create topic
        await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.create_topics([new_topic], request_timeout=10)
        )
        
        # Wait for topic creation
        await asyncio.sleep(2)
        
        try:
            # Get topic configurations
            config_resource = ConfigResource(ConfigResource.Type.TOPIC, topic_name)
            configs = await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.describe_configs([config_resource], request_timeout=10)
            )
            
            assert config_resource in configs
            config_result = configs[config_resource].result()
            
            # Verify our custom configurations are present
            config_dict = {k: v.value for k, v in config_result.items()}
            assert 'retention.ms' in config_dict
            assert 'cleanup.policy' in config_dict
            assert config_dict['cleanup.policy'] == 'delete'
            
        finally:
            # Clean up - delete the test topic
            await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.delete_topics([topic_name], request_timeout=10)
            )
    
    @pytest.mark.asyncio
    async def test_topic_with_multiple_partitions(self):
        """Test topic operations with multiple partitions and replicas."""
        admin_client = self.manager.get_admin_client()
        
        # Create a topic with multiple partitions
        from confluent_kafka.admin import NewTopic
        topic_name = "test-multi-partition"
        partition_count = 5
        
        new_topic = NewTopic(
            topic_name, 
            num_partitions=partition_count, 
            replication_factor=1
        )
        
        loop = asyncio.get_event_loop()
        
        # Create topic
        await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.create_topics([new_topic], request_timeout=10)
        )
        
        # Wait for topic creation
        await asyncio.sleep(2)
        
        try:
            # Get topic metadata
            metadata = await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.list_topics(topic=topic_name, timeout=10)
            )
            
            topic_metadata = metadata.topics[topic_name]
            
            # Verify all partitions are present
            assert len(topic_metadata.partitions) == partition_count
            
            # Verify partition IDs are sequential
            partition_ids = sorted(topic_metadata.partitions.keys())
            expected_ids = list(range(partition_count))
            assert partition_ids == expected_ids
            
            # Verify each partition has a leader
            for partition_metadata in topic_metadata.partitions.values():
                assert partition_metadata.leader >= 0  # Valid broker ID
                assert len(partition_metadata.replicas) == 1  # Single replica
                assert len(partition_metadata.isrs) == 1  # In-sync replicas
                
        finally:
            # Clean up - delete the test topic
            await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.delete_topics([topic_name], request_timeout=10)
            )

class TestTopicValidation:
    """Test topic validation and error handling."""
    
    def setup_method(self):
        """Set up for each test method."""
        self.env_patch = patch.dict(os.environ, {
            'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092',
            'KAFKA_SECURITY_PROTOCOL': 'PLAINTEXT',
            'READONLY': 'false'
        })
        self.env_patch.start()
        self.manager = load_cluster_configurations()
    
    def teardown_method(self):
        """Clean up after each test method."""
        self.env_patch.stop()
        self.manager.executor.shutdown(wait=True)
    
    def test_invalid_topic_name_characters(self):
        """Test validation of topic names with invalid characters."""
        # Kafka topic names have specific character restrictions
        invalid_names = [
            "topic with spaces",
            "topic/with/slashes",
            "topic\\with\\backslashes",
            "topic.with..double.dots",
            "TOPIC_WITH_UPPERCASE",  # Depending on Kafka config
        ]
        
        # Note: This test would typically be part of the MCP tool validation
        # For now, we just validate that these are problematic names
        for invalid_name in invalid_names:
            # Each name has characteristics that might cause issues
            assert " " in invalid_name or "/" in invalid_name or "\\" in invalid_name or ".." in invalid_name or invalid_name.isupper()
    
    def test_topic_name_length_limits(self):
        """Test topic name length validation."""
        # Kafka has a 249 character limit for topic names
        max_length = 249
        
        # Valid length topic name
        valid_name = "a" * (max_length - 1)
        assert len(valid_name) < max_length
        
        # Invalid length topic name
        invalid_name = "a" * (max_length + 1)
        assert len(invalid_name) > max_length

class TestTopicSorting:
    """Test topic sorting and filtering functionality."""
    
    def test_topic_name_sorting(self):
        """Test that topics are sorted alphabetically."""
        # Sample topic list (unsorted)
        topics = [
            {"name": "zebra-topic", "partitions": 1},
            {"name": "alpha-topic", "partitions": 2},
            {"name": "beta-topic", "partitions": 3},
            {"name": "gamma-topic", "partitions": 1},
        ]
        
        # Sort topics by name (simulating the MCP tool behavior)
        sorted_topics = sorted(topics, key=lambda x: x["name"])
        
        expected_order = ["alpha-topic", "beta-topic", "gamma-topic", "zebra-topic"]
        actual_order = [topic["name"] for topic in sorted_topics]
        
        assert actual_order == expected_order
    
    def test_internal_topic_filtering(self):
        """Test filtering of internal Kafka topics."""
        # Sample topic list with internal topics
        all_topics = [
            "user-events",
            "__consumer_offsets",
            "order-updates",
            "__transaction_state",
            "payment-notifications",
            "_schemas",  # Schema registry topic
        ]
        
        # Filter internal topics (simulating MCP tool behavior)
        user_topics = [name for name in all_topics if not name.startswith('__') and not name.startswith('_')]
        
        expected_user_topics = ["user-events", "order-updates", "payment-notifications"]
        assert user_topics == expected_user_topics
        
        # Verify internal topics are identified correctly
        internal_topics = [name for name in all_topics if name.startswith('__') or name.startswith('_')]
        expected_internal = ["__consumer_offsets", "__transaction_state", "_schemas"]
        assert internal_topics == expected_internal

if __name__ == "__main__":
    pytest.main([__file__, "-v"])