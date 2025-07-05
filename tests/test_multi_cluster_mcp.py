#!/usr/bin/env python3
"""
Multi-Cluster MCP Tests
Tests for multi-cluster functionality including configuration, operations, and cross-cluster comparisons.
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
    KafkaClusterConfig, 
    KafkaClusterManager, 
    load_cluster_configurations
)

class TestMultiClusterConfiguration:
    """Test multi-cluster configuration loading and management."""
    
    def test_multi_cluster_config_loading(self):
        """Test loading multiple cluster configurations from environment."""
        with patch.dict(os.environ, {
            'KAFKA_CLUSTER_NAME_1': 'development',
            'KAFKA_BOOTSTRAP_SERVERS_1': 'dev-kafka:9092',
            'KAFKA_SECURITY_PROTOCOL_1': 'PLAINTEXT',
            'READONLY_1': 'false',
            
            'KAFKA_CLUSTER_NAME_2': 'staging',
            'KAFKA_BOOTSTRAP_SERVERS_2': 'staging-kafka:9092',
            'KAFKA_SECURITY_PROTOCOL_2': 'SASL_PLAINTEXT',
            'KAFKA_SASL_MECHANISM_2': 'PLAIN',
            'READONLY_2': 'false',
            
            'KAFKA_CLUSTER_NAME_3': 'production',
            'KAFKA_BOOTSTRAP_SERVERS_3': 'prod-kafka:9092',
            'KAFKA_SECURITY_PROTOCOL_3': 'SASL_SSL',
            'KAFKA_SASL_MECHANISM_3': 'SCRAM-SHA-256',
            'KAFKA_SASL_USERNAME_3': 'prod-user',
            'KAFKA_SASL_PASSWORD_3': 'prod-password',
            'READONLY_3': 'true',
        }, clear=True):
            manager = load_cluster_configurations()
            
            # Should have loaded 3 clusters
            assert len(manager.clusters) == 3
            
            # Verify each cluster is configured correctly
            dev_config = manager.get_cluster_config('development')
            assert dev_config.name == 'development'
            assert dev_config.bootstrap_servers == 'dev-kafka:9092'
            assert dev_config.security_protocol == 'PLAINTEXT'
            assert dev_config.readonly is False
            
            staging_config = manager.get_cluster_config('staging')
            assert staging_config.name == 'staging'
            assert staging_config.bootstrap_servers == 'staging-kafka:9092'
            assert staging_config.security_protocol == 'SASL_PLAINTEXT'
            assert staging_config.sasl_mechanism == 'PLAIN'
            assert staging_config.readonly is False
            
            prod_config = manager.get_cluster_config('production')
            assert prod_config.name == 'production'
            assert prod_config.bootstrap_servers == 'prod-kafka:9092'
            assert prod_config.security_protocol == 'SASL_SSL'
            assert prod_config.sasl_mechanism == 'SCRAM-SHA-256'
            assert prod_config.sasl_username == 'prod-user'
            assert prod_config.sasl_password == 'prod-password'
            assert prod_config.readonly is True
    
    def test_partial_cluster_configuration(self):
        """Test loading when only some clusters are configured."""
        with patch.dict(os.environ, {
            'KAFKA_CLUSTER_NAME_1': 'cluster1',
            'KAFKA_BOOTSTRAP_SERVERS_1': 'kafka1:9092',
            
            'KAFKA_CLUSTER_NAME_3': 'cluster3',  # Skip cluster 2
            'KAFKA_BOOTSTRAP_SERVERS_3': 'kafka3:9092',
            
            'KAFKA_CLUSTER_NAME_5': 'cluster5',  # Skip cluster 4
            'KAFKA_BOOTSTRAP_SERVERS_5': 'kafka5:9092',
        }, clear=True):
            manager = load_cluster_configurations()
            
            # Should have loaded 3 clusters (1, 3, 5)
            assert len(manager.clusters) == 3
            assert 'cluster1' in manager.clusters
            assert 'cluster3' in manager.clusters
            assert 'cluster5' in manager.clusters
            
            # Should not have clusters 2 or 4
            assert 'cluster2' not in manager.clusters
            assert 'cluster4' not in manager.clusters
    
    def test_max_cluster_limit(self):
        """Test that we support up to 8 clusters."""
        env_vars = {}
        
        # Configure 8 clusters
        for i in range(1, 9):
            env_vars[f'KAFKA_CLUSTER_NAME_{i}'] = f'cluster{i}'
            env_vars[f'KAFKA_BOOTSTRAP_SERVERS_{i}'] = f'kafka{i}:9092'
        
        # Try to configure a 9th cluster (should be ignored)
        env_vars['KAFKA_CLUSTER_NAME_9'] = 'cluster9'
        env_vars['KAFKA_BOOTSTRAP_SERVERS_9'] = 'kafka9:9092'
        
        with patch.dict(os.environ, env_vars, clear=True):
            manager = load_cluster_configurations()
            
            # Should have exactly 8 clusters (9th should be ignored)
            assert len(manager.clusters) == 8
            
            # Verify all 8 clusters are present
            for i in range(1, 9):
                assert f'cluster{i}' in manager.clusters
            
            # 9th cluster should not be present
            assert 'cluster9' not in manager.clusters
    
    def test_cluster_with_missing_name_or_servers(self):
        """Test that clusters with missing name or servers are skipped."""
        with patch.dict(os.environ, {
            'KAFKA_CLUSTER_NAME_1': 'valid-cluster',
            'KAFKA_BOOTSTRAP_SERVERS_1': 'kafka1:9092',
            
            # Missing servers for cluster 2
            'KAFKA_CLUSTER_NAME_2': 'missing-servers',
            # No KAFKA_BOOTSTRAP_SERVERS_2
            
            # Missing name for cluster 3
            # No KAFKA_CLUSTER_NAME_3
            'KAFKA_BOOTSTRAP_SERVERS_3': 'kafka3:9092',
            
            'KAFKA_CLUSTER_NAME_4': 'another-valid',
            'KAFKA_BOOTSTRAP_SERVERS_4': 'kafka4:9092',
        }, clear=True):
            manager = load_cluster_configurations()
            
            # Should have loaded only the valid clusters (1 and 4)
            assert len(manager.clusters) == 2
            assert 'valid-cluster' in manager.clusters
            assert 'another-valid' in manager.clusters
            
            # Invalid clusters should not be present
            assert 'missing-servers' not in manager.clusters

class TestMultiClusterOperations:
    """Test operations across multiple clusters."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        # Check if both Kafka clusters are available
        try:
            # Test cluster 1
            result1 = subprocess.run([
                'docker-compose', '-f', 'docker-compose.test.yml', 
                'exec', '-T', 'kafka', 
                'kafka-topics', '--bootstrap-server', 'localhost:9092', '--list'
            ], capture_output=True, text=True, timeout=10)
            
            # Test cluster 2
            result2 = subprocess.run([
                'docker-compose', '-f', 'docker-compose.test.yml', 
                'exec', '-T', 'kafka-cluster-2', 
                'kafka-topics', '--bootstrap-server', 'localhost:9093', '--list'
            ], capture_output=True, text=True, timeout=10)
            
            if result1.returncode != 0 or result2.returncode != 0:
                pytest.skip("Multi-cluster test environment not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker or Kafka not available for integration tests")
    
    def setup_method(self):
        """Set up for each test method."""
        # Configure environment for multi-cluster
        self.env_patch = patch.dict(os.environ, {
            'KAFKA_CLUSTER_NAME_1': 'cluster1',
            'KAFKA_BOOTSTRAP_SERVERS_1': 'localhost:9092',
            'KAFKA_SECURITY_PROTOCOL_1': 'PLAINTEXT',
            'READONLY_1': 'false',
            
            'KAFKA_CLUSTER_NAME_2': 'cluster2',
            'KAFKA_BOOTSTRAP_SERVERS_2': 'localhost:9093',
            'KAFKA_SECURITY_PROTOCOL_2': 'PLAINTEXT',
            'READONLY_2': 'false',
        }, clear=True)
        self.env_patch.start()
        
        # Load cluster manager
        self.manager = load_cluster_configurations()
    
    def teardown_method(self):
        """Clean up after each test method."""
        self.env_patch.stop()
        self.manager.executor.shutdown(wait=True)
    
    @pytest.mark.asyncio
    async def test_cluster_specific_operations(self):
        """Test operations on specific clusters."""
        # Test that we can get admin clients for each cluster
        admin_client_1 = self.manager.get_admin_client('cluster1')
        admin_client_2 = self.manager.get_admin_client('cluster2')
        
        assert admin_client_1 is not None
        assert admin_client_2 is not None
        assert admin_client_1 != admin_client_2  # Different clients
        
        loop = asyncio.get_event_loop()
        
        # Get metadata from each cluster
        metadata_1 = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client_1.list_topics(timeout=10)
        )
        
        metadata_2 = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client_2.list_topics(timeout=10)
        )
        
        # Both should succeed
        assert hasattr(metadata_1, 'topics')
        assert hasattr(metadata_2, 'topics')
        
        # They may have different topics (this is expected)
        topics_1 = list(metadata_1.topics.keys())
        topics_2 = list(metadata_2.topics.keys())
        
        assert isinstance(topics_1, list)
        assert isinstance(topics_2, list)
    
    @pytest.mark.asyncio
    async def test_cluster_comparison(self):
        """Test comparing information across clusters."""
        loop = asyncio.get_event_loop()
        
        # Get broker information from both clusters
        admin_client_1 = self.manager.get_admin_client('cluster1')
        admin_client_2 = self.manager.get_admin_client('cluster2')
        
        metadata_1 = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client_1.list_topics(timeout=10)
        )
        
        metadata_2 = await loop.run_in_executor(
            self.manager.executor,
            lambda: admin_client_2.list_topics(timeout=10)
        )
        
        # Compare broker counts
        brokers_1 = len(metadata_1.brokers)
        brokers_2 = len(metadata_2.brokers)
        
        # Both should have at least one broker
        assert brokers_1 >= 1
        assert brokers_2 >= 1
        
        # Compare cluster IDs (should be different)
        cluster_id_1 = metadata_1.cluster_id
        cluster_id_2 = metadata_2.cluster_id
        
        # Cluster IDs should be different (if both are set)
        if cluster_id_1 and cluster_id_2:
            assert cluster_id_1 != cluster_id_2
    
    def test_readonly_mode_per_cluster(self):
        """Test that readonly mode can be set per cluster."""
        # Check readonly status for each cluster
        cluster1_readonly = self.manager.is_readonly('cluster1')
        cluster2_readonly = self.manager.is_readonly('cluster2')
        
        # Based on our configuration, both should be writable
        assert cluster1_readonly is False
        assert cluster2_readonly is False
        
        # Test configuration with mixed readonly settings
        with patch.dict(os.environ, {
            'KAFKA_CLUSTER_NAME_1': 'dev',
            'KAFKA_BOOTSTRAP_SERVERS_1': 'localhost:9092',
            'READONLY_1': 'false',
            
            'KAFKA_CLUSTER_NAME_2': 'prod',
            'KAFKA_BOOTSTRAP_SERVERS_2': 'localhost:9093',
            'READONLY_2': 'true',  # Production is readonly
        }, clear=True):
            mixed_manager = load_cluster_configurations()
            
            assert mixed_manager.is_readonly('dev') is False
            assert mixed_manager.is_readonly('prod') is True

class TestMultiClusterErrorHandling:
    """Test error handling in multi-cluster scenarios."""
    
    def test_invalid_cluster_name_access(self):
        """Test accessing a cluster that doesn't exist."""
        with patch.dict(os.environ, {
            'KAFKA_CLUSTER_NAME_1': 'only-cluster',
            'KAFKA_BOOTSTRAP_SERVERS_1': 'localhost:9092',
        }, clear=True):
            manager = load_cluster_configurations()
            
            # Should work for valid cluster
            config = manager.get_cluster_config('only-cluster')
            assert config.name == 'only-cluster'
            
            # Should fail for invalid cluster
            with pytest.raises(ValueError, match="Cluster 'nonexistent' not found"):
                manager.get_cluster_config('nonexistent')
            
            with pytest.raises(ValueError, match="Cluster 'nonexistent' not found"):
                manager.get_admin_client('nonexistent')
    
    def test_ambiguous_default_cluster(self):
        """Test behavior when multiple clusters exist but no specific cluster is requested."""
        with patch.dict(os.environ, {
            'KAFKA_CLUSTER_NAME_1': 'cluster1',
            'KAFKA_BOOTSTRAP_SERVERS_1': 'localhost:9092',
            
            'KAFKA_CLUSTER_NAME_2': 'cluster2',
            'KAFKA_BOOTSTRAP_SERVERS_2': 'localhost:9093',
        }, clear=True):
            manager = load_cluster_configurations()
            
            # Should fail when trying to get default config with multiple clusters
            with pytest.raises(ValueError, match="Multiple clusters available"):
                manager.get_cluster_config()  # No cluster specified
            
            with pytest.raises(ValueError, match="Multiple clusters available"):
                manager.get_admin_client()  # No cluster specified
    
    def test_cluster_with_default_name(self):
        """Test that a cluster named 'default' can be accessed as default."""
        with patch.dict(os.environ, {
            'KAFKA_CLUSTER_NAME_1': 'default',
            'KAFKA_BOOTSTRAP_SERVERS_1': 'localhost:9092',
            
            'KAFKA_CLUSTER_NAME_2': 'other',
            'KAFKA_BOOTSTRAP_SERVERS_2': 'localhost:9093',
        }, clear=True):
            manager = load_cluster_configurations()
            
            # Should be able to access 'default' cluster without specifying name
            config = manager.get_cluster_config()
            assert config.name == 'default'
            
            admin_client = manager.get_admin_client()
            assert admin_client is not None
            
            # Should also be able to access it by name
            config_by_name = manager.get_cluster_config('default')
            assert config_by_name.name == 'default'

class TestMultiClusterAuthentication:
    """Test authentication configuration across multiple clusters."""
    
    def test_different_auth_per_cluster(self):
        """Test that different authentication can be configured per cluster."""
        with patch.dict(os.environ, {
            # Cluster 1: No authentication
            'KAFKA_CLUSTER_NAME_1': 'dev',
            'KAFKA_BOOTSTRAP_SERVERS_1': 'dev-kafka:9092',
            'KAFKA_SECURITY_PROTOCOL_1': 'PLAINTEXT',
            
            # Cluster 2: SASL/PLAIN
            'KAFKA_CLUSTER_NAME_2': 'staging',
            'KAFKA_BOOTSTRAP_SERVERS_2': 'staging-kafka:9092',
            'KAFKA_SECURITY_PROTOCOL_2': 'SASL_PLAINTEXT',
            'KAFKA_SASL_MECHANISM_2': 'PLAIN',
            'KAFKA_SASL_USERNAME_2': 'staging-user',
            'KAFKA_SASL_PASSWORD_2': 'staging-pass',
            
            # Cluster 3: SASL/SCRAM with SSL
            'KAFKA_CLUSTER_NAME_3': 'prod',
            'KAFKA_BOOTSTRAP_SERVERS_3': 'prod-kafka:9092',
            'KAFKA_SECURITY_PROTOCOL_3': 'SASL_SSL',
            'KAFKA_SASL_MECHANISM_3': 'SCRAM-SHA-256',
            'KAFKA_SASL_USERNAME_3': 'prod-user',
            'KAFKA_SASL_PASSWORD_3': 'prod-password',
        }, clear=True):
            manager = load_cluster_configurations()
            
            # Verify each cluster has different authentication
            dev_config = manager.get_cluster_config('dev')
            assert dev_config.security_protocol == 'PLAINTEXT'
            assert dev_config.sasl_mechanism is None
            assert dev_config.sasl_username is None
            
            staging_config = manager.get_cluster_config('staging')
            assert staging_config.security_protocol == 'SASL_PLAINTEXT'
            assert staging_config.sasl_mechanism == 'PLAIN'
            assert staging_config.sasl_username == 'staging-user'
            assert staging_config.sasl_password == 'staging-pass'
            
            prod_config = manager.get_cluster_config('prod')
            assert prod_config.security_protocol == 'SASL_SSL'
            assert prod_config.sasl_mechanism == 'SCRAM-SHA-256'
            assert prod_config.sasl_username == 'prod-user'
            assert prod_config.sasl_password == 'prod-password'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])