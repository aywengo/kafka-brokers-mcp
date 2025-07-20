#!/usr/bin/env python3
"""
MCP Tools Testing Script
Manual testing script for MCP tools without requiring Claude Desktop.
Useful for development and debugging.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kafka_brokers_unified_mcp import (
    load_cluster_configurations,
    list_clusters,
    list_topics,
    describe_topic,
    list_consumer_groups,
    describe_consumer_group,
    list_brokers,
    get_cluster_metadata,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_json(data: Any, title: str = ""):
    """Print data as formatted JSON."""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))


async def test_basic_tools():
    """Test basic MCP tools."""
    print_section("Testing Basic MCP Tools")

    try:
        # Test list_clusters
        print_section("List Clusters")
        clusters = await list_clusters()
        print_json(clusters, "Available Clusters")

        # Test list_topics
        print_section("List Topics")
        topics = await list_topics()
        print_json(topics, "Topics in Default Cluster")

        # Test list_brokers
        print_section("List Brokers")
        brokers = await list_brokers()
        print_json(brokers, "Brokers in Default Cluster")

        # Test get_cluster_metadata
        print_section("Cluster Metadata")
        metadata = await get_cluster_metadata()
        print_json(metadata, "Cluster Metadata")

        # Test list_consumer_groups
        print_section("List Consumer Groups")
        groups = await list_consumer_groups()
        print_json(groups, "Consumer Groups")

        return True

    except Exception as e:
        print(f"Error during basic testing: {e}")
        return False


async def test_topic_operations():
    """Test topic-specific operations."""
    print_section("Testing Topic Operations")

    try:
        # Get list of topics first
        topics = await list_topics()

        if not topics:
            print("No topics available for testing")
            return True

        # Test describe_topic with the first available topic
        topic_name = topics[0]["name"]
        print(f"\nTesting with topic: {topic_name}")

        topic_details = await describe_topic(topic_name)
        print_json(topic_details, f"Details for topic '{topic_name}'")

        return True

    except Exception as e:
        print(f"Error during topic testing: {e}")
        return False


async def test_consumer_group_operations():
    """Test consumer group operations."""
    print_section("Testing Consumer Group Operations")

    try:
        # Get list of consumer groups
        groups = await list_consumer_groups()

        if not groups:
            print("No consumer groups available for testing")
            return True

        # Test describe_consumer_group with the first available group
        group_id = groups[0]["group_id"]
        print(f"\nTesting with consumer group: {group_id}")

        group_details = await describe_consumer_group(group_id)
        print_json(group_details, f"Details for consumer group '{group_id}'")

        return True

    except Exception as e:
        print(f"Error during consumer group testing: {e}")
        return False


async def test_multi_cluster_operations():
    """Test multi-cluster operations if multiple clusters are configured."""
    print_section("Testing Multi-Cluster Operations")

    try:
        clusters = await list_clusters()

        if len(clusters) < 2:
            print("Only one cluster configured, skipping multi-cluster tests")
            return True

        print(f"Found {len(clusters)} clusters, testing each...")

        for cluster in clusters:
            cluster_name = cluster["name"]
            print(f"\n--- Testing cluster: {cluster_name} ---")

            # Test topics in this cluster
            topics = await list_topics(cluster_name)
            print(f"Topics in {cluster_name}: {len(topics)}")

            # Test brokers in this cluster
            brokers = await list_brokers(cluster_name)
            print(f"Brokers in {cluster_name}: {len(brokers)}")

            # Test metadata for this cluster
            metadata = await get_cluster_metadata(cluster_name)
            print(f"Cluster {cluster_name} metadata: {metadata['cluster_id']}")

        return True

    except Exception as e:
        print(f"Error during multi-cluster testing: {e}")
        return False


def check_environment():
    """Check if environment is properly configured."""
    print_section("Environment Configuration Check")

    # Check for single cluster configuration
    single_cluster = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if single_cluster:
        print(f"Single cluster mode detected: {single_cluster}")
        print(f"Security protocol: {os.getenv('KAFKA_SECURITY_PROTOCOL', 'PLAINTEXT')}")
        print(f"Readonly mode: {os.getenv('READONLY', 'false')}")
        return True

    # Check for multi-cluster configuration
    cluster_count = 0
    for i in range(1, 9):
        name = os.getenv(f"KAFKA_CLUSTER_NAME_{i}")
        servers = os.getenv(f"KAFKA_BOOTSTRAP_SERVERS_{i}")
        if name and servers:
            cluster_count += 1
            print(f"Cluster {i}: {name} -> {servers}")
            readonly = os.getenv(f"READONLY_{i}", "false")
            print(f"  Readonly: {readonly}")

    if cluster_count > 0:
        print(f"\nMulti-cluster mode detected: {cluster_count} clusters")
        return True

    print("No Kafka cluster configuration found!")
    print("Please set either:")
    print("  KAFKA_BOOTSTRAP_SERVERS for single cluster")
    print("  or KAFKA_CLUSTER_NAME_X/KAFKA_BOOTSTRAP_SERVERS_X for multi-cluster")
    return False


async def run_all_tests():
    """Run all tests in sequence."""
    print_section("Kafka Brokers MCP Server - Tool Testing")

    # Check environment configuration
    if not check_environment():
        return False

    # Initialize cluster manager
    try:
        manager = load_cluster_configurations()
        print(f"\nSuccessfully loaded {len(manager.clusters)} cluster(s)")
        for name in manager.clusters.keys():
            print(f"  - {name}")
    except Exception as e:
        print(f"Failed to load cluster configurations: {e}")
        return False

    # Run tests
    tests = [
        ("Basic Tools", test_basic_tools),
        ("Topic Operations", test_topic_operations),
        ("Consumer Group Operations", test_consumer_group_operations),
        ("Multi-Cluster Operations", test_multi_cluster_operations),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n\n🔍 Running: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))

    # Print summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! MCP tools are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check configuration and Kafka connectivity.")

    return passed == total


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python test_mcp_tools.py")
        print("")
        print("This script tests MCP tools functionality without requiring Claude Desktop.")
        print("")
        print("Environment Variables:")
        print("  Single cluster:")
        print("    KAFKA_BOOTSTRAP_SERVERS - Kafka broker endpoints")
        print("    KAFKA_SECURITY_PROTOCOL - Security protocol (default: PLAINTEXT)")
        print("    READONLY - Enable readonly mode (default: false)")
        print("")
        print("  Multi-cluster:")
        print("    KAFKA_CLUSTER_NAME_X - Cluster name (X=1-8)")
        print("    KAFKA_BOOTSTRAP_SERVERS_X - Cluster endpoints")
        print("    READONLY_X - Per-cluster readonly mode")
        return

    try:
        # Run the async test suite
        result = asyncio.run(run_all_tests())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
