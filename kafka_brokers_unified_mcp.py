#!/usr/bin/env python3
"""
Kafka Brokers MCP Server
A comprehensive MCP server for Kafka broker operations using confluent-kafka-python.
Supports single and multi-cluster configurations with viewonly mode protection.
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

# Import modules
from kafka_cluster_manager import load_cluster_configurations
import kafka_mcp_resources as resources
import kafka_mcp_tools as tools

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize the cluster manager
cluster_manager = load_cluster_configurations()

# Set cluster manager for modules
resources.set_cluster_manager(cluster_manager)
tools.set_cluster_manager(cluster_manager)

# Create the MCP server
mcp = FastMCP("Kafka Brokers MCP Server")


# Register MCP Resources
@mcp.resource("kafka://cluster-status")
async def get_cluster_status() -> str:
    return await resources.get_cluster_status()


@mcp.resource("kafka://cluster-info")
async def get_cluster_info() -> str:
    return await resources.get_cluster_info()


@mcp.resource("kafka://brokers")
async def get_brokers_resource() -> str:
    return await resources.get_brokers_resource()


@mcp.resource("kafka://topics")
async def get_topics_resource() -> str:
    return await resources.get_topics_resource()


@mcp.resource("kafka://consumer-groups")
async def get_consumer_groups_resource() -> str:
    return await resources.get_consumer_groups_resource()


@mcp.resource("kafka://partitions")
async def get_partitions_resource() -> str:
    return await resources.get_partitions_resource()


@mcp.resource("kafka://brokers/{name}")
async def get_cluster_brokers_resource(name: str) -> str:
    return await resources.get_cluster_brokers_resource(name)


@mcp.resource("kafka://topics/{name}")
async def get_cluster_topics_resource(name: str) -> str:
    return await resources.get_cluster_topics_resource(name)


@mcp.resource("kafka://consumer-groups/{name}")
async def get_cluster_consumer_groups_resource(name: str) -> str:
    return await resources.get_cluster_consumer_groups_resource(name)


@mcp.resource("kafka://partitions/{name}")
async def get_cluster_partitions_resource(name: str) -> str:
    return await resources.get_cluster_partitions_resource(name)


@mcp.resource("kafka://cluster-health/{name}")
async def get_cluster_health_resource(name: str) -> str:
    return await resources.get_cluster_health_resource(name)


# Register MCP Tools
@mcp.tool()
async def list_clusters():
    return await tools.list_clusters()


@mcp.tool()
async def list_topics(cluster=None):
    return await tools.list_topics(cluster)


@mcp.tool()
async def describe_topic(topic_name: str, cluster=None):
    return await tools.describe_topic(topic_name, cluster)


@mcp.tool()
async def list_consumer_groups(cluster=None):
    return await tools.list_consumer_groups(cluster)


@mcp.tool()
async def describe_consumer_group(group_id: str, cluster=None):
    return await tools.describe_consumer_group(group_id, cluster)


@mcp.tool()
async def list_brokers(cluster=None):
    return await tools.list_brokers(cluster)


@mcp.tool()
async def get_cluster_metadata(cluster=None):
    return await tools.get_cluster_metadata(cluster)


@mcp.tool()
async def get_partitions(cluster=None, topic=None):
    return await tools.get_partitions(cluster, topic)


@mcp.tool()
async def get_cluster_health(cluster: str):
    return await tools.get_cluster_health(cluster)


@mcp.tool()
async def compare_cluster_topics(source_cluster: str, target_cluster: str):
    return await tools.compare_cluster_topics(source_cluster, target_cluster)


@mcp.tool()
async def get_partition_leaders(cluster_name: str):
    return await tools.get_partition_leaders(cluster_name)


@mcp.tool()
async def get_topic_partition_details(cluster_name: str, topic_name: str):
    return await tools.get_topic_partition_details(cluster_name, topic_name)


@mcp.tool()
async def find_under_replicated_partitions(cluster_name: str):
    return await tools.find_under_replicated_partitions(cluster_name)


@mcp.tool()
async def get_broker_partition_count(cluster_name: str):
    return await tools.get_broker_partition_count(cluster_name)


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
