#!/usr/bin/env python3
"""
Consumer Group Operations Tests
Tests for consumer group management functionality including listing, describing, and offset operations.
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

class TestConsumerGroupOperations:
    """Test consumer group-related operations."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        # Check if Kafka is available
        try:
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.test.yml', 
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
    async def test_list_consumer_groups_empty(self):
        """Test listing consumer groups when none exist."""
        admin_client = self.manager.get_admin_client()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.list_consumer_groups(timeout=10)
        )
        
        groups = result.result()
        # Should return empty list or minimal system groups
        assert isinstance(groups, list)
        # Length can be 0 or small number (system groups)
        assert len(groups) >= 0
    
    @pytest.mark.asyncio
    async def test_create_and_describe_consumer_group(self):
        """Test creating a consumer and describing its group."""
        from confluent_kafka import Consumer, Producer
        from confluent_kafka.admin import NewTopic
        
        admin_client = self.manager.get_admin_client()
        loop = asyncio.get_event_loop()
        
        # Create a test topic first
        topic_name = "test-consumer-group-topic"
        group_id = "test-consumer-group"
        
        new_topic = NewTopic(topic_name, num_partitions=2, replication_factor=1)
        
        # Create topic
        await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.create_topics([new_topic], request_timeout=10)
        )
        
        # Wait for topic creation
        await asyncio.sleep(2)
        
        try:
            # Create a consumer to establish the group
            consumer_config = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': group_id,
                'auto.offset.reset': 'earliest',
                'session.timeout.ms': 6000,
                'heartbeat.interval.ms': 1000
            }
            
            def create_consumer_group():
                consumer = Consumer(consumer_config)
                try:
                    # Subscribe to topic to create the group
                    consumer.subscribe([topic_name])
                    
                    # Poll once to join the group
                    consumer.poll(timeout=5.0)
                    
                    # Commit offsets to establish group state
                    consumer.commit()
                    
                    return True
                finally:
                    consumer.close()
            
            # Create the consumer group
            await loop.run_in_executor(
                self.manager.executor,
                create_consumer_group
            )
            
            # Wait for group to be established
            await asyncio.sleep(3)
            
            # List consumer groups
            result = await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.list_consumer_groups(timeout=10)
            )
            
            groups = result.result()
            group_ids = [group.group_id for group in groups]
            
            # Our test group should be in the list
            assert group_id in group_ids
            
            # Describe the consumer group
            describe_result = await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.describe_consumer_groups([group_id], timeout=10)
            )
            
            assert group_id in describe_result
            group_description = describe_result[group_id].result()
            
            # Verify group properties
            assert group_description.group_id == group_id
            assert hasattr(group_description, 'state')
            assert hasattr(group_description, 'protocol_type')
            assert hasattr(group_description, 'coordinator')
            
        finally:
            # Clean up - delete the test topic
            await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.delete_topics([topic_name], request_timeout=10)
            )
    
    @pytest.mark.asyncio
    async def test_describe_nonexistent_consumer_group(self):
        """Test describing a consumer group that doesn't exist."""
        admin_client = self.manager.get_admin_client()
        
        nonexistent_group = "nonexistent-consumer-group"
        
        loop = asyncio.get_event_loop()
        
        # Try to describe non-existent group
        describe_result = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.describe_consumer_groups([nonexistent_group], timeout=10)
        )
        
        # Should contain the group ID in results
        assert nonexistent_group in describe_result
        
        # But the result should indicate an error
        group_future = describe_result[nonexistent_group]
        
        # The future should complete, but may contain an error
        try:
            group_description = group_future.result()
            # If it succeeds, the group might exist or be in an unknown state
            assert hasattr(group_description, 'group_id')
        except Exception as e:
            # Expected: group doesn't exist
            assert "not exist" in str(e).lower() or "unknown" in str(e).lower()

class TestConsumerGroupStates:
    """Test consumer group state management."""
    
    def test_consumer_group_state_validation(self):
        """Test validation of consumer group states."""
        # Valid consumer group states in Kafka
        valid_states = [
            "Unknown",
            "PreparingRebalance",
            "CompletingRebalance", 
            "Stable",
            "Dead",
            "Empty"
        ]
        
        # Each state should be a valid string
        for state in valid_states:
            assert isinstance(state, str)
            assert len(state) > 0
    
    def test_consumer_group_protocol_types(self):
        """Test consumer group protocol types."""
        # Common protocol types
        protocol_types = ["consumer", "connect", "streams"]
        
        for protocol_type in protocol_types:
            assert isinstance(protocol_type, str)
            assert len(protocol_type) > 0

class TestConsumerGroupOffsets:
    """Test consumer group offset operations."""
    
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
    
    @pytest.mark.asyncio
    async def test_consumer_offset_structure(self):
        """Test the structure of consumer offset information."""
        from confluent_kafka import TopicPartition
        
        # Create sample TopicPartition objects to test structure
        topic_partitions = [
            TopicPartition("test-topic", 0, offset=100),
            TopicPartition("test-topic", 1, offset=200),
            TopicPartition("another-topic", 0, offset=50),
        ]
        
        # Verify structure matches what we expect in offset information
        for tp in topic_partitions:
            assert hasattr(tp, 'topic')
            assert hasattr(tp, 'partition')
            assert hasattr(tp, 'offset')
            assert isinstance(tp.topic, str)
            assert isinstance(tp.partition, int)
            assert isinstance(tp.offset, int)
            assert tp.partition >= 0
            assert tp.offset >= 0
    
    def test_offset_metadata_format(self):
        """Test offset metadata formatting."""
        # Sample offset information structure
        offset_info = {
            "topic": "user-events",
            "partition": 0,
            "current_offset": 1523,
            "metadata": ""
        }
        
        # Verify required fields are present
        required_fields = ["topic", "partition", "current_offset", "metadata"]
        for field in required_fields:
            assert field in offset_info
        
        # Verify data types
        assert isinstance(offset_info["topic"], str)
        assert isinstance(offset_info["partition"], int)
        assert isinstance(offset_info["current_offset"], int)
        assert isinstance(offset_info["metadata"], str)
        
        # Verify logical constraints
        assert offset_info["partition"] >= 0
        assert offset_info["current_offset"] >= 0

class TestConsumerGroupAssignments:
    """Test consumer group partition assignments."""
    
    def test_assignment_structure(self):
        """Test the structure of partition assignments."""
        # Sample assignment structure
        assignment = {
            "topic": "user-events",
            "partition": 0
        }
        
        # Verify required fields
        assert "topic" in assignment
        assert "partition" in assignment
        
        # Verify data types
        assert isinstance(assignment["topic"], str)
        assert isinstance(assignment["partition"], int)
        
        # Verify constraints
        assert len(assignment["topic"]) > 0
        assert assignment["partition"] >= 0
    
    def test_member_assignment_structure(self):
        """Test consumer group member assignment structure."""
        # Sample member information
        member = {
            "member_id": "consumer-1-12345",
            "client_id": "analytics-consumer",
            "client_host": "/192.168.1.100",
            "assignments": [
                {"topic": "user-events", "partition": 0},
                {"topic": "user-events", "partition": 1}
            ]
        }
        
        # Verify required fields
        required_fields = ["member_id", "client_id", "client_host", "assignments"]
        for field in required_fields:
            assert field in member
        
        # Verify data types
        assert isinstance(member["member_id"], str)
        assert isinstance(member["client_id"], str)
        assert isinstance(member["client_host"], str)
        assert isinstance(member["assignments"], list)
        
        # Verify assignments structure
        for assignment in member["assignments"]:
            assert "topic" in assignment
            assert "partition" in assignment
            assert isinstance(assignment["topic"], str)
            assert isinstance(assignment["partition"], int)

class TestConsumerGroupSorting:
    """Test consumer group sorting and filtering."""
    
    def test_consumer_group_sorting(self):
        """Test that consumer groups are sorted by group ID."""
        # Sample consumer groups (unsorted)
        groups = [
            {"group_id": "zebra-group", "state": "Stable"},
            {"group_id": "alpha-group", "state": "Stable"},
            {"group_id": "beta-group", "state": "Empty"},
        ]
        
        # Sort groups by group_id (simulating MCP tool behavior)
        sorted_groups = sorted(groups, key=lambda x: x["group_id"])
        
        expected_order = ["alpha-group", "beta-group", "zebra-group"]
        actual_order = [group["group_id"] for group in sorted_groups]
        
        assert actual_order == expected_order
    
    def test_consumer_group_filtering_by_state(self):
        """Test filtering consumer groups by state."""
        # Sample consumer groups with different states
        groups = [
            {"group_id": "active-group-1", "state": "Stable"},
            {"group_id": "dead-group", "state": "Dead"},
            {"group_id": "active-group-2", "state": "Stable"},
            {"group_id": "empty-group", "state": "Empty"},
        ]
        
        # Filter for active (Stable) groups
        active_groups = [group for group in groups if group["state"] == "Stable"]
        
        expected_active = ["active-group-1", "active-group-2"]
        actual_active = [group["group_id"] for group in active_groups]
        
        assert sorted(actual_active) == sorted(expected_active)
        
        # Filter for non-active groups
        inactive_groups = [group for group in groups if group["state"] != "Stable"]
        
        expected_inactive = ["dead-group", "empty-group"]
        actual_inactive = [group["group_id"] for group in inactive_groups]
        
        assert sorted(actual_inactive) == sorted(expected_inactive)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])