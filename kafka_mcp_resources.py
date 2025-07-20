"""
Kafka MCP Resources Module
Defines all MCP resources (kafka:// endpoints) for cluster status, brokers, topics, etc.
"""

import json
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kafka_cluster_manager import KafkaClusterManager

# Global cluster manager - will be set by main module
cluster_manager: "KafkaClusterManager" = None


def set_cluster_manager(manager: "KafkaClusterManager"):
    """Set the global cluster manager instance."""
    global cluster_manager
    cluster_manager = manager


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


async def get_brokers_resource() -> str:
    """Get all brokers across all clusters as a resource."""
    brokers_data = {"brokers": {}, "timestamp": time.time()}

    for cluster_name in cluster_manager.clusters.keys():
        try:
            admin_client = cluster_manager.get_admin_client(cluster_name)
            metadata = admin_client.list_topics(timeout=10)

            brokers_data["brokers"][cluster_name] = []
            for broker_id, broker_metadata in metadata.brokers.items():
                brokers_data["brokers"][cluster_name].append(
                    {
                        "broker_id": broker_id,
                        "host": broker_metadata.host,
                        "port": broker_metadata.port,
                        "rack": getattr(broker_metadata, "rack", None),
                        "cluster": cluster_name,
                    }
                )

        except Exception as e:
            brokers_data["brokers"][cluster_name] = {"error": str(e), "status": "failed"}

    return json.dumps(brokers_data, indent=2)


async def get_topics_resource() -> str:
    """Get all topics across all clusters as a resource."""
    topics_data = {"topics": {}, "timestamp": time.time()}

    for cluster_name in cluster_manager.clusters.keys():
        try:
            admin_client = cluster_manager.get_admin_client(cluster_name)
            metadata = admin_client.list_topics(timeout=10)

            topics_data["topics"][cluster_name] = []
            for topic_name, topic_metadata in metadata.topics.items():
                if not topic_name.startswith("__"):  # Filter internal topics
                    topics_data["topics"][cluster_name].append(
                        {
                            "name": topic_name,
                            "partitions": len(topic_metadata.partitions),
                            "replication_factor": (
                                len(topic_metadata.partitions[0].replicas) if topic_metadata.partitions else 0
                            ),
                            "internal": False,
                            "cluster": cluster_name,
                        }
                    )

        except Exception as e:
            topics_data["topics"][cluster_name] = {"error": str(e), "status": "failed"}

    return json.dumps(topics_data, indent=2)


async def get_consumer_groups_resource() -> str:
    """Get all consumer groups across all clusters as a resource."""
    groups_data = {"consumer_groups": {}, "timestamp": time.time()}

    for cluster_name in cluster_manager.clusters.keys():
        try:
            admin_client = cluster_manager.get_admin_client(cluster_name)
            result = admin_client.list_consumer_groups(timeout=10)

            groups_data["consumer_groups"][cluster_name] = []
            for group in result.result():
                groups_data["consumer_groups"][cluster_name].append(
                    {
                        "group_id": group.group_id,
                        "is_simple_consumer_group": group.is_simple_consumer_group,
                        "state": group.state.name if hasattr(group, "state") else "UNKNOWN",
                        "cluster": cluster_name,
                    }
                )

        except Exception as e:
            groups_data["consumer_groups"][cluster_name] = {"error": str(e), "status": "failed"}

    return json.dumps(groups_data, indent=2)


async def get_partitions_resource() -> str:
    """Get all partitions across all clusters as a resource."""
    partitions_data = {"partitions": {}, "timestamp": time.time()}

    for cluster_name in cluster_manager.clusters.keys():
        try:
            admin_client = cluster_manager.get_admin_client(cluster_name)
            metadata = admin_client.list_topics(timeout=10)

            partitions_data["partitions"][cluster_name] = []
            for topic_name, topic_metadata in metadata.topics.items():
                if not topic_name.startswith("__"):  # Filter internal topics
                    for partition_id, partition_metadata in topic_metadata.partitions.items():
                        partitions_data["partitions"][cluster_name].append(
                            {
                                "topic": topic_name,
                                "partition_id": partition_id,
                                "leader": partition_metadata.leader,
                                "replicas": partition_metadata.replicas,
                                "in_sync_replicas": partition_metadata.isrs,
                                "error": str(partition_metadata.error) if partition_metadata.error else None,
                                "cluster": cluster_name,
                            }
                        )

        except Exception as e:
            partitions_data["partitions"][cluster_name] = {"error": str(e), "status": "failed"}

    return json.dumps(partitions_data, indent=2)


async def get_cluster_brokers_resource(name: str) -> str:
    """Get brokers for a specific cluster."""
    try:
        admin_client = cluster_manager.get_admin_client(name)
        metadata = admin_client.list_topics(timeout=10)

        brokers_data = {"cluster": name, "brokers": [], "timestamp": time.time()}

        for broker_id, broker_metadata in metadata.brokers.items():
            brokers_data["brokers"].append(
                {
                    "broker_id": broker_id,
                    "host": broker_metadata.host,
                    "port": broker_metadata.port,
                    "rack": getattr(broker_metadata, "rack", None),
                    "cluster": name,
                }
            )

        return json.dumps(brokers_data, indent=2)

    except Exception as e:
        error_data = {"cluster": name, "error": str(e), "status": "failed", "timestamp": time.time()}
        return json.dumps(error_data, indent=2)


async def get_cluster_topics_resource(name: str) -> str:
    """Get topics for a specific cluster."""
    try:
        admin_client = cluster_manager.get_admin_client(name)
        metadata = admin_client.list_topics(timeout=10)

        topics_data = {"cluster": name, "topics": [], "timestamp": time.time()}

        for topic_name, topic_metadata in metadata.topics.items():
            if not topic_name.startswith("__"):  # Filter internal topics
                topics_data["topics"].append(
                    {
                        "name": topic_name,
                        "partitions": len(topic_metadata.partitions),
                        "replication_factor": len(topic_metadata.partitions[0].replicas) if topic_metadata.partitions else 0,
                        "internal": False,
                        "cluster": name,
                    }
                )

        return json.dumps(topics_data, indent=2)

    except Exception as e:
        error_data = {"cluster": name, "error": str(e), "status": "failed", "timestamp": time.time()}
        return json.dumps(error_data, indent=2)


async def get_cluster_consumer_groups_resource(name: str) -> str:
    """Get consumer groups for a specific cluster."""
    try:
        admin_client = cluster_manager.get_admin_client(name)
        result = admin_client.list_consumer_groups(timeout=10)

        groups_data = {"cluster": name, "consumer_groups": [], "timestamp": time.time()}

        for group in result.result():
            groups_data["consumer_groups"].append(
                {
                    "group_id": group.group_id,
                    "is_simple_consumer_group": group.is_simple_consumer_group,
                    "state": group.state.name if hasattr(group, "state") else "UNKNOWN",
                    "cluster": name,
                }
            )

        return json.dumps(groups_data, indent=2)

    except Exception as e:
        error_data = {"cluster": name, "error": str(e), "status": "failed", "timestamp": time.time()}
        return json.dumps(error_data, indent=2)


async def get_cluster_partitions_resource(name: str) -> str:
    """Get partitions for a specific cluster."""
    try:
        admin_client = cluster_manager.get_admin_client(name)
        metadata = admin_client.list_topics(timeout=10)

        partitions_data = {"cluster": name, "partitions": [], "timestamp": time.time()}

        for topic_name, topic_metadata in metadata.topics.items():
            if not topic_name.startswith("__"):  # Filter internal topics
                for partition_id, partition_metadata in topic_metadata.partitions.items():
                    partitions_data["partitions"].append(
                        {
                            "topic": topic_name,
                            "partition_id": partition_id,
                            "leader": partition_metadata.leader,
                            "replicas": partition_metadata.replicas,
                            "in_sync_replicas": partition_metadata.isrs,
                            "error": str(partition_metadata.error) if partition_metadata.error else None,
                            "cluster": name,
                        }
                    )

        return json.dumps(partitions_data, indent=2)

    except Exception as e:
        error_data = {"cluster": name, "error": str(e), "status": "failed", "timestamp": time.time()}
        return json.dumps(error_data, indent=2)


async def get_cluster_health_resource(name: str) -> str:
    """Get comprehensive health information for a specific cluster."""
    try:
        admin_client = cluster_manager.get_admin_client(name)
        config = cluster_manager.get_cluster_config(name)
        metadata = admin_client.list_topics(timeout=10)

        # Calculate health metrics
        total_topics = len([t for t in metadata.topics.keys() if not t.startswith("__")])
        total_partitions = sum(len(topic.partitions) for topic in metadata.topics.values() if not topic.name.startswith("__"))

        # Check for partition issues
        unhealthy_partitions = 0
        for topic_metadata in metadata.topics.values():
            if not topic_metadata.name.startswith("__"):
                for partition_metadata in topic_metadata.partitions.values():
                    if partition_metadata.error or len(partition_metadata.isrs) < len(partition_metadata.replicas):
                        unhealthy_partitions += 1

        health_data = {
            "cluster": name,
            "health_status": "healthy" if unhealthy_partitions == 0 else "degraded",
            "cluster_info": {
                "cluster_id": metadata.cluster_id,
                "controller_id": metadata.controller_id,
                "bootstrap_servers": config.bootstrap_servers,
                "viewonly": config.viewonly,
            },
            "metrics": {
                "broker_count": len(metadata.brokers),
                "topic_count": total_topics,
                "partition_count": total_partitions,
                "unhealthy_partitions": unhealthy_partitions,
                "health_percentage": round((total_partitions - unhealthy_partitions) / max(total_partitions, 1) * 100, 2),
            },
            "timestamp": time.time(),
        }

        return json.dumps(health_data, indent=2)

    except Exception as e:
        error_data = {"cluster": name, "error": str(e), "status": "failed", "timestamp": time.time()}
        return json.dumps(error_data, indent=2)
