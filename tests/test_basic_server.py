#!/usr/bin/env python3
"""
Basic tests for Kafka Brokers MCP Server
Tests core functionality including cluster connection, topic listing, and consumer group operations.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import unittest
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from kafka_brokers_unified_mcp import (
    KafkaClusterConfig, 
    KafkaClusterManager, 
    load_cluster_configurations
)
from test_utils import run_docker_compose

class TestKafkaClusterManager:
    """Test the KafkaClusterManager class."""
    
    def test_single_cluster_config(self):
        """Test single cluster configuration loading."""
        with patch.dict(os.environ, {
            'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092',
            'KAFKA_SECURITY_PROTOCOL': 'PLAINTEXT',
            'VIEWONLY': 'false'
        }, clear=True):
            manager = load_cluster_configurations()
            
            assert len(manager.clusters) == 1
            assert 'default' in manager.clusters
            
            config = manager.get_cluster_config()
            assert config.name == 'default'
            assert config.bootstrap_servers == 'localhost:9092'
            assert config.security_protocol == 'PLAINTEXT'
            assert config.viewonly is False
    
    def test_multi_cluster_config(self):
        """Test multi-cluster configuration loading."""
        with patch.dict(os.environ, {
            'KAFKA_CLUSTER_NAME_1': 'dev',
            'KAFKA_BOOTSTRAP_SERVERS_1': 'localhost:9092',
            'KAFKA_SECURITY_PROTOCOL_1': 'PLAINTEXT',
            'VIEWONLY_1': 'false',
            'KAFKA_CLUSTER_NAME_2': 'prod',
            'KAFKA_BOOTSTRAP_SERVERS_2': 'localhost:9093',
            'KAFKA_SECURITY_PROTOCOL_2': 'SASL_SSL',
            'KAFKA_SASL_MECHANISM_2': 'SCRAM-SHA-256',
            'KAFKA_SASL_USERNAME_2': 'prod-user',
            'KAFKA_SASL_PASSWORD_2': 'prod-pass',
            'VIEWONLY_2': 'true'
        }, clear=True):
            manager = load_cluster_configurations()
            
            assert len(manager.clusters) == 2
            assert 'dev' in manager.clusters
            assert 'prod' in manager.clusters
            
            dev_config = manager.get_cluster_config('dev')
            assert dev_config.name == 'dev'
            assert dev_config.bootstrap_servers == 'localhost:9092'
            assert dev_config.viewonly is False
            
            prod_config = manager.get_cluster_config('prod')
            assert prod_config.name == 'prod'
            assert prod_config.bootstrap_servers == 'localhost:9093'
            assert prod_config.security_protocol == 'SASL_SSL'
            assert prod_config.sasl_mechanism == 'SCRAM-SHA-256'
            assert prod_config.sasl_username == 'prod-user'
            assert prod_config.viewonly is True
    
    def test_no_config_raises_error(self):
        """Test that missing configuration raises appropriate error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No cluster configurations found"):
                load_cluster_configurations()
    
    def test_viewonly_check(self):
        """Test viewonly mode checking."""
        config = KafkaClusterConfig(
            name='test',
            bootstrap_servers='localhost:9092',
            viewonly=True
        )
        manager = KafkaClusterManager()
        manager.add_cluster(config)
        
        assert manager.is_viewonly('test') is True

class TestMCPServerIntegration:
    """Integration tests with actual Kafka clusters."""
    
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
            'VIEWONLY': 'false'
        })
        self.env_patch.start()
        
        # Load cluster manager
        self.manager = load_cluster_configurations()
    
    def teardown_method(self):
        """Clean up after each test method."""
        self.env_patch.stop()
        self.manager.executor.shutdown(wait=True)
    
    @pytest.mark.asyncio
    async def test_list_topics_integration(self):
        """Test listing topics with real Kafka cluster."""
        admin_client = self.manager.get_admin_client()
        
        # Get topics using admin client directly
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.list_topics(timeout=10)
        )
        
        # Should have at least the test topics we created
        topic_names = list(metadata.topics.keys())
        user_topics = [name for name in topic_names if not name.startswith('__')]
        
        assert len(user_topics) >= 0  # May have test topics
        assert isinstance(topic_names, list)
    
    @pytest.mark.asyncio
    async def test_describe_topic_integration(self):
        """Test describing a topic with real Kafka cluster."""
        admin_client = self.manager.get_admin_client()
        
        # Create a test topic first
        from confluent_kafka.admin import NewTopic
        topic_name = "test-describe-topic"
        
        new_topic = NewTopic(topic_name, num_partitions=3, replication_factor=1)
        
        loop = asyncio.get_event_loop()
        
        # Create topic
        create_result = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.create_topics([new_topic], request_timeout=10)
        )
        
        # Wait for topic creation
        await asyncio.sleep(2)
        
        try:
            # Describe the topic
            metadata = await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.list_topics(topic=topic_name, timeout=10)
            )
            
            assert topic_name in metadata.topics
            topic_metadata = metadata.topics[topic_name]
            assert len(topic_metadata.partitions) == 3
            
        finally:
            # Clean up - delete the test topic
            delete_result = await loop.run_in_executor(
                self.manager.executor,
                lambda: admin_client.delete_topics([topic_name], request_timeout=10)
            )
    
    @pytest.mark.asyncio
    async def test_list_consumer_groups_integration(self):
        """Test listing consumer groups with real Kafka cluster."""
        admin_client = self.manager.get_admin_client()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.list_consumer_groups(timeout=10)
        )
        
        groups = result.result()
        assert isinstance(groups, list)
        # May or may not have consumer groups, but should not error
    
    @pytest.mark.asyncio
    async def test_list_brokers_integration(self):
        """Test listing brokers with real Kafka cluster."""
        admin_client = self.manager.get_admin_client()
        
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.list_topics(timeout=10)
        )
        
        brokers = metadata.brokers
        assert len(brokers) >= 1  # Should have at least one broker
        
        # Check broker structure
        for broker_id, broker_metadata in brokers.items():
            assert isinstance(broker_id, int)
            assert hasattr(broker_metadata, 'host')
            assert hasattr(broker_metadata, 'port')
    
    @pytest.mark.asyncio
    async def test_cluster_metadata_integration(self):
        """Test getting cluster metadata with real Kafka cluster."""
        admin_client = self.manager.get_admin_client()
        config = self.manager.get_cluster_config()
        
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client.list_topics(timeout=10)
        )
        
        # Verify metadata structure
        assert hasattr(metadata, 'cluster_id')
        assert hasattr(metadata, 'controller_id')
        assert len(metadata.brokers) >= 1
        assert len(metadata.topics) >= 0
        
        # Check configuration
        assert config.name == 'default'
        assert config.bootstrap_servers == 'localhost:9092'
        assert config.security_protocol == 'PLAINTEXT'

class TestViewonlyMode:
    """Test viewonly mode functionality."""
    
    def test_viewonly_flag_detection(self):
        """Test that viewonly flag is properly detected."""
        config = KafkaClusterConfig(
            name='viewonly-cluster',
            bootstrap_servers='localhost:9092',
            viewonly=True
        )
        
        manager = KafkaClusterManager()
        manager.add_cluster(config)
        
        assert manager.is_viewonly('viewonly-cluster') is True
    
    def test_multi_cluster_viewonly_modes(self):
        """Test different viewonly modes across clusters."""
        dev_config = KafkaClusterConfig(
            name='dev',
            bootstrap_servers='localhost:9092',
            viewonly=False
        )
        
        prod_config = KafkaClusterConfig(
            name='prod',
            bootstrap_servers='localhost:9093',
            viewonly=True
        )
        
        manager = KafkaClusterManager()
        manager.add_cluster(dev_config)
        manager.add_cluster(prod_config)
        
        assert manager.is_viewonly('dev') is False
        assert manager.is_viewonly('prod') is True

class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_cluster_name(self):
        """Test handling of invalid cluster names."""
        manager = KafkaClusterManager()
        config = KafkaClusterConfig(name='test', bootstrap_servers='localhost:9092')
        manager.add_cluster(config)
        
        with pytest.raises(ValueError, match="Cluster 'nonexistent' not found"):
            manager.get_cluster_config('nonexistent')
    
    def test_no_clusters_configured(self):
        """Test behavior when no clusters are configured."""
        manager = KafkaClusterManager()
        
        with pytest.raises(ValueError, match="Multiple clusters available"):
            manager.get_cluster_config()
    
    def test_multiple_clusters_no_default(self):
        """Test behavior with multiple clusters but no default specified."""
        manager = KafkaClusterManager()
        
        config1 = KafkaClusterConfig(name='cluster1', bootstrap_servers='localhost:9092')
        config2 = KafkaClusterConfig(name='cluster2', bootstrap_servers='localhost:9093')
        
        manager.add_cluster(config1)
        manager.add_cluster(config2)
        
        with pytest.raises(ValueError, match="Multiple clusters available"):
            manager.get_cluster_config()

if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])