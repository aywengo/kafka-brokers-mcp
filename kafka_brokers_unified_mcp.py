#!/usr/bin/env python3
"""
Kafka Brokers MCP Server
A comprehensive MCP server for Kafka broker operations using confluent-kafka-python.
Supports single and multi-cluster configurations with viewonly mode protection.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time

from confluent_kafka import Consumer, Producer, TopicPartition
from confluent_kafka.admin import AdminClient, ConfigResource, NewTopic
from mcp.server.fastmcp import FastMCP
from mcp.server.models import InitializationOptions
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class KafkaClusterConfig:
    """Configuration for a Kafka cluster connection."""

    name: str
    bootstrap_servers: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_ca_location: Optional[str] = None
    ssl_certificate_location: Optional[str] = None
    ssl_key_location: Optional[str] = None
    viewonly: bool = False


class KafkaClusterManager:
    """Manages Kafka cluster connections and operations."""

    def __init__(self):
        self.clusters: Dict[str, KafkaClusterConfig] = {}
        self.admin_clients: Dict[str, AdminClient] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

    def add_cluster(self, config: KafkaClusterConfig):
        """Add a cluster configuration."""
        self.clusters[config.name] = config
        self._create_admin_client(config)

    def _create_admin_client(self, config: KafkaClusterConfig):
        """Create an AdminClient for the cluster."""
        kafka_config = {
            "bootstrap.servers": config.bootstrap_servers,
            "security.protocol": config.security_protocol,
        }

        if config.sasl_mechanism:
            kafka_config["sasl.mechanism"] = config.sasl_mechanism
        if config.sasl_username:
            kafka_config["sasl.username"] = config.sasl_username
        if config.sasl_password:
            kafka_config["sasl.password"] = config.sasl_password
        if config.ssl_ca_location:
            kafka_config["ssl.ca.location"] = config.ssl_ca_location
        if config.ssl_certificate_location:
            kafka_config["ssl.certificate.location"] = config.ssl_certificate_location
        if config.ssl_key_location:
            kafka_config["ssl.key.location"] = config.ssl_key_location

        self.admin_clients[config.name] = AdminClient(kafka_config)

    def get_admin_client(self, cluster_name: Optional[str] = None) -> AdminClient:
        """Get AdminClient for specified cluster or default."""
        if cluster_name is None:
            if len(self.admin_clients) == 1:
                return list(self.admin_clients.values())[0]
            elif "default" in self.admin_clients:
                return self.admin_clients["default"]
            else:
                raise ValueError("Multiple clusters available, please specify cluster_name")

        if cluster_name not in self.admin_clients:
            raise ValueError(f"Cluster '{cluster_name}' not found")

        return self.admin_clients[cluster_name]

    def get_cluster_config(self, cluster_name: Optional[str] = None) -> KafkaClusterConfig:
        """Get cluster configuration."""
        if cluster_name is None:
            if len(self.clusters) == 1:
                return list(self.clusters.values())[0]
            elif "default" in self.clusters:
                return self.clusters["default"]
            else:
                raise ValueError("Multiple clusters available, please specify cluster_name")

        if cluster_name not in self.clusters:
            raise ValueError(f"Cluster '{cluster_name}' not found")

        return self.clusters[cluster_name]

    def is_viewonly(self, cluster_name: Optional[str] = None) -> bool:
        """Check if cluster is in viewonly mode."""
        config = self.get_cluster_config(cluster_name)
        return config.viewonly


def load_cluster_configurations() -> KafkaClusterManager:
    """Load cluster configurations from environment variables."""
    manager = KafkaClusterManager()

    # Check for single cluster mode first
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if bootstrap_servers:
        config = KafkaClusterConfig(
            name="default",
            bootstrap_servers=bootstrap_servers,
            security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
            sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
            sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
            ssl_ca_location=os.getenv("KAFKA_SSL_CA_LOCATION"),
            ssl_certificate_location=os.getenv("KAFKA_SSL_CERTIFICATE_LOCATION"),
            ssl_key_location=os.getenv("KAFKA_SSL_KEY_LOCATION"),
            viewonly=os.getenv("VIEWONLY", "false").lower() == "true",
        )
        manager.add_cluster(config)
        logger.info(f"Loaded single cluster configuration: {bootstrap_servers}")
        return manager

    # Check for multi-cluster mode
    for i in range(1, 9):  # Support up to 8 clusters
        name = os.getenv(f"KAFKA_CLUSTER_NAME_{i}")
        servers = os.getenv(f"KAFKA_BOOTSTRAP_SERVERS_{i}")

        if name and servers:
            config = KafkaClusterConfig(
                name=name,
                bootstrap_servers=servers,
                security_protocol=os.getenv(f"KAFKA_SECURITY_PROTOCOL_{i}", "PLAINTEXT"),
                sasl_mechanism=os.getenv(f"KAFKA_SASL_MECHANISM_{i}"),
                sasl_username=os.getenv(f"KAFKA_SASL_USERNAME_{i}"),
                sasl_password=os.getenv(f"KAFKA_SASL_PASSWORD_{i}"),
                ssl_ca_location=os.getenv(f"KAFKA_SSL_CA_LOCATION_{i}"),
                ssl_certificate_location=os.getenv(f"KAFKA_SSL_CERTIFICATE_LOCATION_{i}"),
                ssl_key_location=os.getenv(f"KAFKA_SSL_KEY_LOCATION_{i}"),
                viewonly=os.getenv(f"VIEWONLY_{i}", "false").lower() == "true",
            )
            manager.add_cluster(config)
            logger.info(f"Loaded cluster configuration: {name} -> {servers}")

    if not manager.clusters:
        raise ValueError(
            "No cluster configurations found. Set KAFKA_BOOTSTRAP_SERVERS or KAFKA_CLUSTER_NAME_X/KAFKA_BOOTSTRAP_SERVERS_X"
        )

    return manager


# Initialize the cluster manager
cluster_manager = load_cluster_configurations()

# Create the MCP server
mcp = FastMCP("Kafka Brokers MCP Server")


@mcp.resource("kafka://cluster-status")
async def get_cluster_status() -> str:
    """Get real-time cluster status information."""
    status = {"clusters": {}, "timestamp": time.time()}

    for name, config in cluster_manager.clusters.items():
        try:
            admin_client = cluster_manager.get_admin_client(name)
            metadata = admin_client.list_topics(timeout=10)

            status["clusters"][name] = {
                "name": name,
                "bootstrap_servers": config.bootstrap_servers,
                "viewonly": config.viewonly,
                "topics_count": len(metadata.topics),
                "brokers_count": len(metadata.brokers),
                "status": "healthy",
            }
        except Exception as e:
            status["clusters"][name] = {
                "name": name,
                "bootstrap_servers": config.bootstrap_servers,
                "viewonly": config.viewonly,
                "status": "error",
                "error": str(e),
            }

    return json.dumps(status, indent=2)


@mcp.resource("kafka://cluster-info")
async def get_cluster_info() -> str:
    """Get detailed cluster configuration information."""
    info = {
        "server_version": "1.0.0",
        "clusters": {},
        "configuration": {
            "viewonly_protection": any(c.viewonly for c in cluster_manager.clusters.values()),
            "multi_cluster_mode": len(cluster_manager.clusters) > 1,
            "total_clusters": len(cluster_manager.clusters),
        },
    }

    for name, config in cluster_manager.clusters.items():
        info["clusters"][name] = {
            "name": config.name,
            "bootstrap_servers": config.bootstrap_servers,
            "security_protocol": config.security_protocol,
            "viewonly": config.viewonly,
            "authentication": {
                "sasl_mechanism": config.sasl_mechanism,
                "has_credentials": bool(config.sasl_username),
            },
        }

    return json.dumps(info, indent=2)


# MCP Tools Implementation


@mcp.tool()
async def list_clusters() -> List[Dict[str, Any]]:
    """List all configured Kafka clusters."""
    clusters = []
    for name, config in cluster_manager.clusters.items():
        try:
            admin_client = cluster_manager.get_admin_client(name)
            metadata = admin_client.list_topics(timeout=10)

            clusters.append(
                {
                    "name": name,
                    "bootstrap_servers": config.bootstrap_servers,
                    "security_protocol": config.security_protocol,
                    "viewonly": config.viewonly,
                    "topics_count": len(metadata.topics),
                    "brokers_count": len(metadata.brokers),
                    "status": "healthy",
                }
            )
        except Exception as e:
            clusters.append(
                {
                    "name": name,
                    "bootstrap_servers": config.bootstrap_servers,
                    "viewonly": config.viewonly,
                    "status": "error",
                    "error": str(e),
                }
            )

    return clusters


@mcp.tool()
async def list_topics(cluster: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all topics in the specified cluster."""
    try:
        admin_client = cluster_manager.get_admin_client(cluster)

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(cluster_manager.executor, lambda: admin_client.list_topics(timeout=10))

        topics = []
        for topic_name, topic_metadata in metadata.topics.items():
            if not topic_name.startswith("__"):  # Filter internal topics
                topics.append(
                    {
                        "name": topic_name,
                        "partitions": len(topic_metadata.partitions),
                        "replication_factor": len(topic_metadata.partitions[0].replicas) if topic_metadata.partitions else 0,
                        "internal": False,
                    }
                )

        return sorted(topics, key=lambda x: x["name"])

    except Exception as e:
        logger.error(f"Error listing topics: {e}")
        raise


@mcp.tool()
async def describe_topic(topic_name: str, cluster: Optional[str] = None) -> Dict[str, Any]:
    """Get detailed information about a specific topic."""
    try:
        admin_client = cluster_manager.get_admin_client(cluster)

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(
            cluster_manager.executor, lambda: admin_client.list_topics(topic=topic_name, timeout=10)
        )

        if topic_name not in metadata.topics:
            raise ValueError(f"Topic '{topic_name}' not found")

        topic_metadata = metadata.topics[topic_name]

        # Get topic configurations
        config_resource = ConfigResource(ConfigResource.Type.TOPIC, topic_name)
        configs = await loop.run_in_executor(
            cluster_manager.executor,
            lambda: admin_client.describe_configs([config_resource], request_timeout=10),
        )

        topic_configs = {}
        if config_resource in configs:
            config_result = configs[config_resource].result()
            topic_configs = {k: v.value for k, v in config_result.items()}

        # Build partition details
        partitions = []
        for partition_id, partition_metadata in topic_metadata.partitions.items():
            partitions.append(
                {
                    "partition_id": partition_id,
                    "leader": partition_metadata.leader,
                    "replicas": partition_metadata.replicas,
                    "in_sync_replicas": partition_metadata.isrs,
                    "error": str(partition_metadata.error) if partition_metadata.error else None,
                }
            )

        return {
            "name": topic_name,
            "partitions": sorted(partitions, key=lambda x: x["partition_id"]),
            "partition_count": len(partitions),
            "replication_factor": len(partitions[0]["replicas"]) if partitions else 0,
            "configurations": topic_configs,
            "internal": topic_metadata.error is not None,
        }

    except Exception as e:
        logger.error(f"Error describing topic {topic_name}: {e}")
        raise


@mcp.tool()
async def list_consumer_groups(cluster: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all consumer groups in the specified cluster."""
    try:
        admin_client = cluster_manager.get_admin_client(cluster)

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(cluster_manager.executor, lambda: admin_client.list_consumer_groups(timeout=10))

        groups = []
        for group in result.result():
            groups.append(
                {
                    "group_id": group.group_id,
                    "is_simple_consumer_group": group.is_simple_consumer_group,
                    "state": group.state.name if hasattr(group, "state") else "UNKNOWN",
                }
            )

        return sorted(groups, key=lambda x: x["group_id"])

    except Exception as e:
        logger.error(f"Error listing consumer groups: {e}")
        raise


@mcp.tool()
async def describe_consumer_group(group_id: str, cluster: Optional[str] = None) -> Dict[str, Any]:
    """Get detailed information about a specific consumer group."""
    try:
        admin_client = cluster_manager.get_admin_client(cluster)

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()

        # Describe the consumer group
        result = await loop.run_in_executor(
            cluster_manager.executor, lambda: admin_client.describe_consumer_groups([group_id], timeout=10)
        )

        if group_id not in result:
            raise ValueError(f"Consumer group '{group_id}' not found")

        group_description = result[group_id].result()

        # Get consumer group offsets
        def get_offsets():
            # Create a temporary consumer to get committed offsets
            consumer_config = {
                "bootstrap.servers": cluster_manager.get_cluster_config(cluster).bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
            }

            config = cluster_manager.get_cluster_config(cluster)
            if config.security_protocol != "PLAINTEXT":
                consumer_config["security.protocol"] = config.security_protocol
                if config.sasl_mechanism:
                    consumer_config["sasl.mechanism"] = config.sasl_mechanism
                if config.sasl_username:
                    consumer_config["sasl.username"] = config.sasl_username
                if config.sasl_password:
                    consumer_config["sasl.password"] = config.sasl_password

            consumer = Consumer(consumer_config)
            try:
                # Get list of topics this group is consuming from
                metadata = admin_client.list_topics(timeout=10)
                all_partitions = []

                for topic_name in metadata.topics:
                    topic_partitions = consumer.list_consumer_group_offsets([group_id], [TopicPartition(topic_name)])
                    if topic_partitions:
                        all_partitions.extend(topic_partitions)

                committed_offsets = consumer.committed(all_partitions, timeout=10)
                return committed_offsets
            finally:
                consumer.close()

        offsets = await loop.run_in_executor(cluster_manager.executor, get_offsets)

        # Format member information
        members = []
        for member in group_description.members:
            members.append(
                {
                    "member_id": member.member_id,
                    "client_id": member.client_id,
                    "client_host": member.client_host,
                    "assignments": (
                        [{"topic": tp.topic, "partition": tp.partition} for tp in member.assignment.topic_partitions]
                        if member.assignment
                        else []
                    ),
                }
            )

        # Format offset information
        offset_info = []
        for tp in offsets:
            if tp.offset >= 0:  # Valid offset
                offset_info.append(
                    {
                        "topic": tp.topic,
                        "partition": tp.partition,
                        "current_offset": tp.offset,
                        "metadata": tp.metadata,
                    }
                )

        return {
            "group_id": group_id,
            "state": group_description.state.name,
            "protocol_type": group_description.protocol_type,
            "protocol": group_description.protocol,
            "coordinator": {
                "id": group_description.coordinator.id,
                "host": group_description.coordinator.host,
                "port": group_description.coordinator.port,
            },
            "members": members,
            "member_count": len(members),
            "offsets": offset_info,
        }

    except Exception as e:
        logger.error(f"Error describing consumer group {group_id}: {e}")
        raise


@mcp.tool()
async def list_brokers(cluster: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all brokers in the specified cluster."""
    try:
        admin_client = cluster_manager.get_admin_client(cluster)

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(cluster_manager.executor, lambda: admin_client.list_topics(timeout=10))

        brokers = []
        for broker_id, broker_metadata in metadata.brokers.items():
            brokers.append(
                {
                    "broker_id": broker_id,
                    "host": broker_metadata.host,
                    "port": broker_metadata.port,
                    "rack": getattr(broker_metadata, "rack", None),
                }
            )

        return sorted(brokers, key=lambda x: x["broker_id"])

    except Exception as e:
        logger.error(f"Error listing brokers: {e}")
        raise


@mcp.tool()
async def get_cluster_metadata(cluster: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive cluster metadata and information."""
    try:
        admin_client = cluster_manager.get_admin_client(cluster)
        config = cluster_manager.get_cluster_config(cluster)

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(cluster_manager.executor, lambda: admin_client.list_topics(timeout=10))

        # Count topics (excluding internal ones)
        user_topics = [name for name in metadata.topics.keys() if not name.startswith("__")]
        internal_topics = [name for name in metadata.topics.keys() if name.startswith("__")]

        # Calculate total partitions
        total_partitions = sum(len(topic.partitions) for topic in metadata.topics.values())

        return {
            "cluster_name": config.name,
            "bootstrap_servers": config.bootstrap_servers,
            "viewonly": config.viewonly,
            "cluster_id": metadata.cluster_id,
            "controller_id": metadata.controller_id,
            "brokers": {"count": len(metadata.brokers), "ids": list(metadata.brokers.keys())},
            "topics": {
                "total": len(metadata.topics),
                "user_topics": len(user_topics),
                "internal_topics": len(internal_topics),
                "total_partitions": total_partitions,
            },
            "security": {
                "protocol": config.security_protocol,
                "sasl_mechanism": config.sasl_mechanism,
                "authentication_enabled": bool(config.sasl_username),
            },
        }

    except Exception as e:
        logger.error(f"Error getting cluster metadata: {e}")
        raise


# Main function
def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("Starting Kafka Brokers MCP Server...")
        logger.info(f"Configured clusters: {list(cluster_manager.clusters.keys())}")

        # Test cluster connections
        for name in cluster_manager.clusters.keys():
            try:
                admin_client = cluster_manager.get_admin_client(name)
                metadata = admin_client.list_topics(timeout=5)
                logger.info(f"Successfully connected to cluster '{name}' - {len(metadata.topics)} topics found")
            except Exception as e:
                logger.warning(f"Failed to connect to cluster '{name}': {e}")

        # Run the MCP server
        mcp.run()

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        cluster_manager.executor.shutdown(wait=True)


if __name__ == "__main__":
    main()
