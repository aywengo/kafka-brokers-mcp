"""
Kafka MCP Tools Module
Defines all MCP tools (@mcp.tool functions) for Kafka operations.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from confluent_kafka import Consumer, TopicPartition
from confluent_kafka.admin import ConfigResource

import kafka_mcp_resources
from kafka_mcp_resources import get_cluster_partitions_resource, get_partitions_resource, get_cluster_health_resource

if TYPE_CHECKING:
    from kafka_cluster_manager import KafkaClusterManager

# Configure logging
logger = logging.getLogger(__name__)

# Global cluster manager - will be set by main module
cluster_manager: "KafkaClusterManager" = None


def set_cluster_manager(manager: "KafkaClusterManager"):
    """Set the global cluster manager instance."""
    global cluster_manager
    cluster_manager = manager


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


async def list_topics(cluster: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all topics in the specified cluster or all clusters if none specified."""
    try:
        if cluster is None:
            # Get topics from all clusters using resource
            topics_json = await kafka_mcp_resources.get_topics_resource()
            topics_data = json.loads(topics_json)

            # Check for errors in resource response
            if "error" in topics_data:
                raise ValueError(f"Error getting topics: {topics_data['error']}")

            all_topics = []
            for cluster_name, cluster_topics in topics_data.get("topics", {}).items():
                if isinstance(cluster_topics, list):
                    all_topics.extend(cluster_topics)
                elif isinstance(cluster_topics, dict) and "error" in cluster_topics:
                    logger.error(f"Error getting topics from cluster '{cluster_name}': {cluster_topics['error']}")
                    continue

            return sorted(all_topics, key=lambda x: (x.get("cluster", ""), x.get("name", "")))
        else:
            # Get topics from specific cluster using cluster-specific resource
            cluster_topics_json = await kafka_mcp_resources.get_cluster_topics_resource(cluster)
            cluster_data = json.loads(cluster_topics_json)

            # Check for errors in resource response
            if "error" in cluster_data:
                raise ValueError(f"Failed to get topics for cluster '{cluster}': {cluster_data['error']}")

            topics = cluster_data.get("topics", [])
            return sorted(topics, key=lambda x: x.get("name", ""))

    except Exception as e:
        logger.error(f"Error listing topics: {e}")
        raise


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


async def list_consumer_groups(cluster: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all consumer groups in the specified cluster or all clusters if none specified."""
    try:
        if cluster is None:
            # Get consumer groups from all clusters using resource
            groups_json = await kafka_mcp_resources.get_consumer_groups_resource()
            groups_data = json.loads(groups_json)

            # Check for errors in resource response
            if "error" in groups_data:
                raise ValueError(f"Error getting consumer groups: {groups_data['error']}")

            all_groups = []
            for cluster_name, cluster_groups in groups_data.get("consumer_groups", {}).items():
                if isinstance(cluster_groups, list):
                    all_groups.extend(cluster_groups)
                elif isinstance(cluster_groups, dict) and "error" in cluster_groups:
                    logger.error(f"Error getting consumer groups from cluster '{cluster_name}': {cluster_groups['error']}")
                    continue

            return sorted(all_groups, key=lambda x: (x.get("cluster", ""), x.get("group_id", "")))
        else:
            # Get consumer groups from specific cluster using cluster-specific resource
            cluster_groups_json = await kafka_mcp_resources.get_cluster_consumer_groups_resource(cluster)
            cluster_data = json.loads(cluster_groups_json)

            # Check for errors in resource response
            if "error" in cluster_data:
                raise ValueError(f"Failed to get consumer groups for cluster '{cluster}': {cluster_data['error']}")

            groups = cluster_data.get("consumer_groups", [])
            return sorted(groups, key=lambda x: x.get("group_id", ""))

    except Exception as e:
        logger.error(f"Error listing consumer groups: {e}")
        raise


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


async def list_brokers(cluster: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all brokers in the specified cluster or all clusters if none specified."""
    try:
        if cluster is None:
            # Get brokers from all clusters using resource
            brokers_json = await kafka_mcp_resources.get_brokers_resource()
            brokers_data = json.loads(brokers_json)

            # Check for errors in resource response
            if "error" in brokers_data:
                raise ValueError(f"Error getting brokers: {brokers_data['error']}")

            all_brokers = []
            for cluster_name, cluster_brokers in brokers_data.get("brokers", {}).items():
                if isinstance(cluster_brokers, list):
                    all_brokers.extend(cluster_brokers)
                elif isinstance(cluster_brokers, dict) and "error" in cluster_brokers:
                    logger.error(f"Error getting brokers from cluster '{cluster_name}': {cluster_brokers['error']}")
                    continue

            return sorted(all_brokers, key=lambda x: (x.get("cluster", ""), x.get("broker_id", 0)))
        else:
            # Get brokers from specific cluster using cluster-specific resource
            cluster_brokers_json = await kafka_mcp_resources.get_cluster_brokers_resource(cluster)
            cluster_data = json.loads(cluster_brokers_json)

            # Check for errors in resource response
            if "error" in cluster_data:
                raise ValueError(f"Failed to get brokers for cluster '{cluster}': {cluster_data['error']}")

            brokers = cluster_data.get("brokers", [])
            return sorted(brokers, key=lambda x: x.get("broker_id", 0))

    except Exception as e:
        logger.error(f"Error listing brokers: {e}")
        raise


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


async def get_partitions(cluster: Optional[str] = None, topic: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get partitions from kafka://partitions resource or cluster-specific resource."""
    try:
        if cluster:
            # Use cluster-specific resource
            partitions_resource = await kafka_mcp_resources.get_cluster_partitions_resource(cluster)
            partitions_data = json.loads(partitions_resource)

            if "error" in partitions_data:
                raise ValueError(f"Failed to get partitions for cluster '{cluster}': {partitions_data['error']}")

            all_partitions = partitions_data.get("partitions", [])
        else:
            # Use global resource
            partitions_resource = await kafka_mcp_resources.get_partitions_resource()
            partitions_data = json.loads(partitions_resource)

            # Check for errors in resource response
            if "error" in partitions_data:
                raise ValueError(f"Error getting partitions: {partitions_data['error']}")

            all_partitions = []
            for cluster_name, cluster_partitions in partitions_data.get("partitions", {}).items():
                if isinstance(cluster_partitions, list):
                    all_partitions.extend(cluster_partitions)
                elif isinstance(cluster_partitions, dict) and "error" in cluster_partitions:
                    logger.error(f"Error getting partitions from cluster '{cluster_name}': {cluster_partitions['error']}")
                    continue

        # Filter by topic if specified
        if topic:
            all_partitions = [p for p in all_partitions if p["topic"] == topic]

        return sorted(all_partitions, key=lambda x: (x["topic"], x["partition_id"]))

    except Exception as e:
        logger.error(f"Error getting partitions: {e}")
        raise


async def get_cluster_health(cluster: str) -> Dict[str, Any]:
    """Get comprehensive health information for a specific cluster."""
    try:
        health_resource = await kafka_mcp_resources.get_cluster_health_resource(cluster)
        health_data = json.loads(health_resource)

        if "error" in health_data:
            raise ValueError(f"Failed to get health for cluster '{cluster}': {health_data['error']}")

        return health_data

    except Exception as e:
        logger.error(f"Error getting cluster health: {e}")
        raise


async def compare_cluster_topics(source_cluster: str, target_cluster: str) -> Dict[str, Any]:
    """Compare topics between two clusters."""
    try:
        # Get topics from both clusters
        source_topics = await list_topics(cluster=source_cluster)
        target_topics = await list_topics(cluster=target_cluster)

        # Create topic name sets
        source_names = {topic["name"] for topic in source_topics}
        target_names = {topic["name"] for topic in target_topics}

        # Find differences
        only_in_source = source_names - target_names
        only_in_target = target_names - source_names
        common_topics = source_names & target_names

        # Compare common topics
        topic_differences = []
        source_topics_dict = {t["name"]: t for t in source_topics}
        target_topics_dict = {t["name"]: t for t in target_topics}

        for topic_name in common_topics:
            source_topic = source_topics_dict[topic_name]
            target_topic = target_topics_dict[topic_name]

            differences = {}
            if source_topic["partitions"] != target_topic["partitions"]:
                differences["partitions"] = {"source": source_topic["partitions"], "target": target_topic["partitions"]}
            if source_topic["replication_factor"] != target_topic["replication_factor"]:
                differences["replication_factor"] = {
                    "source": source_topic["replication_factor"],
                    "target": target_topic["replication_factor"],
                }

            if differences:
                topic_differences.append({"topic": topic_name, "differences": differences})

        return {
            "source_cluster": source_cluster,
            "target_cluster": target_cluster,
            "summary": {
                "total_source_topics": len(source_names),
                "total_target_topics": len(target_names),
                "common_topics": len(common_topics),
                "only_in_source": len(only_in_source),
                "only_in_target": len(only_in_target),
                "topics_with_differences": len(topic_differences),
            },
            "only_in_source": sorted(list(only_in_source)),
            "only_in_target": sorted(list(only_in_target)),
            "topic_differences": topic_differences,
        }

    except Exception as e:
        logger.error(f"Error comparing cluster topics: {e}")
        raise


async def get_partition_leaders(cluster_name: str) -> Dict[str, Any]:
    """Get partition leader distribution across brokers for a cluster."""
    try:
        partitions = await get_partitions(cluster=cluster_name)
        brokers = await list_brokers(cluster=cluster_name)

        # Count partitions by leader
        leader_counts = {}
        for partition in partitions:
            leader_id = partition["leader"]
            if leader_id not in leader_counts:
                leader_counts[leader_id] = {"broker_id": leader_id, "partition_count": 0, "topics": {}}

            leader_counts[leader_id]["partition_count"] += 1
            topic_name = partition["topic"]
            if topic_name not in leader_counts[leader_id]["topics"]:
                leader_counts[leader_id]["topics"][topic_name] = 0
            leader_counts[leader_id]["topics"][topic_name] += 1

        # Add broker details
        brokers_dict = {b["broker_id"]: b for b in brokers}
        for leader_id, leader_info in leader_counts.items():
            if leader_id in brokers_dict:
                broker = brokers_dict[leader_id]
                leader_info["host"] = broker["host"]
                leader_info["port"] = broker["port"]
                leader_info["rack"] = broker.get("rack")

        return {
            "cluster": cluster_name,
            "total_partitions": len(partitions),
            "total_brokers": len(brokers),
            "leader_distribution": list(leader_counts.values()),
            "balance_ratio": (
                min(leader_counts.values(), key=lambda x: x["partition_count"])["partition_count"]
                / max(leader_counts.values(), key=lambda x: x["partition_count"])["partition_count"]
                if leader_counts
                else 0
            ),
        }

    except Exception as e:
        logger.error(f"Error getting partition leaders: {e}")
        raise


async def get_topic_partition_details(cluster_name: str, topic_name: str) -> Dict[str, Any]:
    """Get detailed partition information for a specific topic."""
    try:
        admin_client = cluster_manager.get_admin_client(cluster_name)

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(
            cluster_manager.executor, lambda: admin_client.list_topics(topic=topic_name, timeout=10)
        )

        if topic_name not in metadata.topics:
            raise ValueError(f"Topic '{topic_name}' not found in cluster '{cluster_name}'")

        topic_metadata = metadata.topics[topic_name]

        # Get brokers info for enrichment
        brokers_dict = {b["broker_id"]: b for b in await list_brokers(cluster=cluster_name)}

        # Build detailed partition info
        partitions_detail = []
        for partition_id, partition_metadata in topic_metadata.partitions.items():
            leader_broker = brokers_dict.get(partition_metadata.leader, {})

            replica_brokers = []
            for replica_id in partition_metadata.replicas:
                broker = brokers_dict.get(replica_id, {})
                replica_brokers.append(
                    {
                        "broker_id": replica_id,
                        "host": broker.get("host", "unknown"),
                        "port": broker.get("port", 0),
                        "in_sync": replica_id in partition_metadata.isrs,
                    }
                )

            partitions_detail.append(
                {
                    "partition_id": partition_id,
                    "leader": {
                        "broker_id": partition_metadata.leader,
                        "host": leader_broker.get("host", "unknown"),
                        "port": leader_broker.get("port", 0),
                    },
                    "replicas": replica_brokers,
                    "replication_factor": len(partition_metadata.replicas),
                    "in_sync_replicas_count": len(partition_metadata.isrs),
                    "is_healthy": len(partition_metadata.isrs) == len(partition_metadata.replicas),
                    "error": str(partition_metadata.error) if partition_metadata.error else None,
                }
            )

        # Calculate topic health
        healthy_partitions = sum(1 for p in partitions_detail if p["is_healthy"])

        return {
            "cluster": cluster_name,
            "topic": topic_name,
            "partition_count": len(partitions_detail),
            "replication_factor": len(partitions_detail[0]["replicas"]) if partitions_detail else 0,
            "health": {
                "healthy_partitions": healthy_partitions,
                "unhealthy_partitions": len(partitions_detail) - healthy_partitions,
                "health_percentage": round(healthy_partitions / len(partitions_detail) * 100, 2) if partitions_detail else 0,
            },
            "partitions": sorted(partitions_detail, key=lambda x: x["partition_id"]),
        }

    except Exception as e:
        logger.error(f"Error getting topic partition details: {e}")
        raise


async def find_under_replicated_partitions(cluster_name: str) -> List[Dict[str, Any]]:
    """Find partitions that are under-replicated (fewer ISRs than replicas)."""
    try:
        partitions = await get_partitions(cluster=cluster_name)

        under_replicated = []
        for partition in partitions:
            isr_count = len(partition["in_sync_replicas"])
            replica_count = len(partition["replicas"])

            if isr_count < replica_count:
                under_replicated.append(
                    {
                        "topic": partition["topic"],
                        "partition_id": partition["partition_id"],
                        "leader": partition["leader"],
                        "replicas": partition["replicas"],
                        "in_sync_replicas": partition["in_sync_replicas"],
                        "missing_replicas": replica_count - isr_count,
                        "replication_factor": replica_count,
                        "cluster": cluster_name,
                    }
                )

        return sorted(under_replicated, key=lambda x: (x["topic"], x["partition_id"]))

    except Exception as e:
        logger.error(f"Error finding under-replicated partitions: {e}")
        raise


async def get_broker_partition_count(cluster_name: str) -> List[Dict[str, Any]]:
    """Get partition count per broker for load balancing analysis."""
    try:
        partitions = await get_partitions(cluster=cluster_name)
        brokers = await list_brokers(cluster=cluster_name)

        # Count partitions per broker (as leader and as replica)
        broker_stats = {}
        for broker in brokers:
            broker_id = broker["broker_id"]
            broker_stats[broker_id] = {
                "broker_id": broker_id,
                "host": broker["host"],
                "port": broker["port"],
                "rack": broker.get("rack"),
                "leader_count": 0,
                "replica_count": 0,
                "topics": set(),
            }

        for partition in partitions:
            # Count leader partitions
            leader_id = partition["leader"]
            if leader_id in broker_stats:
                broker_stats[leader_id]["leader_count"] += 1
                broker_stats[leader_id]["topics"].add(partition["topic"])

            # Count replica partitions
            for replica_id in partition["replicas"]:
                if replica_id in broker_stats:
                    broker_stats[replica_id]["replica_count"] += 1
                    broker_stats[replica_id]["topics"].add(partition["topic"])

        # Convert topics set to count
        for stats in broker_stats.values():
            stats["topic_count"] = len(stats["topics"])
            del stats["topics"]  # Remove the set as it's not JSON serializable

        return sorted(broker_stats.values(), key=lambda x: x["broker_id"])

    except Exception as e:
        logger.error(f"Error getting broker partition count: {e}")
        raise
