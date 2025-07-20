#!/usr/bin/env python3
"""
Create Test Data Script
Creates sample topics and consumer groups for testing the MCP server.
"""

import asyncio
import os
import sys
import time
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from confluent_kafka import Producer, Consumer, TopicPartition
from confluent_kafka.admin import AdminClient, NewTopic


def create_kafka_config(cluster_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create Kafka configuration from cluster config."""
    config = {
        "bootstrap.servers": cluster_config["bootstrap_servers"],
        "security.protocol": cluster_config.get("security_protocol", "PLAINTEXT"),
    }

    if cluster_config.get("sasl_mechanism"):
        config["sasl.mechanism"] = cluster_config["sasl_mechanism"]
    if cluster_config.get("sasl_username"):
        config["sasl.username"] = cluster_config["sasl_username"]
    if cluster_config.get("sasl_password"):
        config["sasl.password"] = cluster_config["sasl_password"]

    return config


def create_topics(admin_client: AdminClient, cluster_name: str) -> List[str]:
    """Create test topics in the cluster."""
    print(f"Creating test topics in cluster '{cluster_name}'...")

    topics_to_create = [
        NewTopic(
            "user-events",
            num_partitions=6,
            replication_factor=1,
            config={"retention.ms": "604800000", "cleanup.policy": "delete"},  # 7 days
        ),
        NewTopic(
            "order-updates",
            num_partitions=3,
            replication_factor=1,
            config={"retention.ms": "86400000", "cleanup.policy": "delete"},  # 1 day
        ),
        NewTopic(
            "payment-notifications",
            num_partitions=2,
            replication_factor=1,
            config={"retention.ms": "2592000000", "cleanup.policy": "delete"},  # 30 days
        ),
        NewTopic(
            "analytics-events",
            num_partitions=4,
            replication_factor=1,
            config={"retention.ms": "2592000000", "cleanup.policy": "delete"},  # 30 days
        ),
        NewTopic(
            "system-logs",
            num_partitions=8,
            replication_factor=1,
            config={"retention.ms": "604800000", "cleanup.policy": "delete"},  # 7 days
        ),
    ]

    # Create topics
    fs = admin_client.create_topics(topics_to_create, request_timeout=30)

    created_topics = []
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print(f"  ✅ Created topic: {topic}")
            created_topics.append(topic)
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"  ⚠️  Topic already exists: {topic}")
                created_topics.append(topic)
            else:
                print(f"  ❌ Failed to create topic {topic}: {e}")

    return created_topics


def produce_sample_messages(producer_config: Dict[str, Any], topics: List[str]):
    """Produce sample messages to topics."""
    print("Producing sample messages...")

    producer = Producer(producer_config)

    # Sample message templates
    message_templates = {
        "user-events": [
            '{"user_id": "user-{}", "event": "login", "timestamp": {}}',
            '{"user_id": "user-{}", "event": "page_view", "page": "/products", "timestamp": {}}',
            '{"user_id": "user-{}", "event": "logout", "timestamp": {}}',
        ],
        "order-updates": [
            '{"order_id": "order-{}", "status": "created", "user_id": "user-{}", "timestamp": {}}',
            '{"order_id": "order-{}", "status": "paid", "amount": {}, "timestamp": {}}',
            '{"order_id": "order-{}", "status": "shipped", "tracking": "TRACK{}", "timestamp": {}}',
        ],
        "payment-notifications": [
            '{"payment_id": "pay-{}", "order_id": "order-{}", "status": "success", "amount": {}, "timestamp": {}}',
            '{"payment_id": "pay-{}", "order_id": "order-{}", "status": "failed", "error": "insufficient_funds", "timestamp": {}}',
        ],
        "analytics-events": [
            '{"session_id": "sess-{}", "event": "conversion", "value": {}, "timestamp": {}}',
            '{"session_id": "sess-{}", "event": "engagement", "duration": {}, "timestamp": {}}',
        ],
        "system-logs": [
            '{"level": "INFO", "service": "api-gateway", "message": "Request processed", "request_id": "req-{}", "timestamp": {}}',
            '{"level": "ERROR", "service": "payment-service", "message": "Database connection failed", "error_id": "err-{}", "timestamp": {}}',
            '{"level": "DEBUG", "service": "user-service", "message": "Cache hit for user {}", "timestamp": {}}',
        ],
    }

    current_time = int(time.time())

    for topic in topics:
        if topic not in message_templates:
            continue

        templates = message_templates[topic]
        messages_per_topic = 20

        print(f"  Producing {messages_per_topic} messages to {topic}...")

        for i in range(messages_per_topic):
            template = templates[i % len(templates)]

            # Fill in template variables
            if topic == "user-events":
                message = template.format(i % 100, current_time + i)
            elif topic == "order-updates":
                message = template.format(i, i % 50, current_time + i, 100 + (i * 10), i, current_time + i)
            elif topic == "payment-notifications":
                message = template.format(i, i % 30, 50 + (i * 5), current_time + i, i, i % 30, current_time + i)
            elif topic == "analytics-events":
                message = template.format(i, 1000 + (i * 10), current_time + i, i, 300 + (i * 5), current_time + i)
            elif topic == "system-logs":
                message = template.format(i, current_time + i, i, current_time + i, i % 100, current_time + i)
            else:
                continue

            try:
                producer.produce(topic=topic, key=f"key-{i}", value=message, partition=i % 3)  # Distribute across partitions
            except Exception as e:
                print(f"    ❌ Error producing to {topic}: {e}")

        # Flush messages
        producer.flush(timeout=10)
        print(f"    ✅ Produced {messages_per_topic} messages to {topic}")

    producer.flush()
    print("  ✅ All messages produced successfully")


def create_consumer_groups(consumer_config: Dict[str, Any], topics: List[str]):
    """Create sample consumer groups."""
    print("Creating sample consumer groups...")

    consumer_groups = [
        {
            "group_id": "analytics-processor",
            "topics": ["user-events", "analytics-events"],
            "description": "Processes user events for analytics",
        },
        {"group_id": "order-fulfillment", "topics": ["order-updates"], "description": "Handles order fulfillment workflow"},
        {
            "group_id": "payment-processor",
            "topics": ["payment-notifications"],
            "description": "Processes payment notifications",
        },
        {"group_id": "monitoring-service", "topics": ["system-logs"], "description": "Monitors system logs for issues"},
        {
            "group_id": "data-pipeline",
            "topics": ["user-events", "order-updates", "payment-notifications"],
            "description": "ETL pipeline for data warehouse",
        },
    ]

    for group_info in consumer_groups:
        group_id = group_info["group_id"]
        group_topics = [t for t in group_info["topics"] if t in topics]

        if not group_topics:
            print(f"  ⚠️  Skipping {group_id}: no matching topics")
            continue

        print(f"  Creating consumer group: {group_id}")

        # Create consumer config for this group
        group_config = consumer_config.copy()
        group_config.update(
            {
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "session.timeout.ms": 30000,
                "heartbeat.interval.ms": 3000,
                "enable.auto.commit": True,
                "auto.commit.interval.ms": 5000,
            }
        )

        try:
            consumer = Consumer(group_config)

            # Subscribe to topics
            consumer.subscribe(group_topics)

            # Poll a few times to join the group and get assignments
            for _ in range(5):
                msg = consumer.poll(timeout=2.0)
                if msg is not None and not msg.error():
                    # Successfully received a message
                    break

            # Commit current offsets to establish the group
            consumer.commit()

            consumer.close()
            print(f"    ✅ Created consumer group: {group_id} (topics: {', '.join(group_topics)})")

        except Exception as e:
            print(f"    ❌ Failed to create consumer group {group_id}: {e}")

    print("  ✅ Consumer group creation completed")


def main():
    """Main entry point."""
    print("Kafka Brokers MCP Server - Test Data Creator")
    print("=" * 50)

    # Check for help
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python create_test_data.py [cluster_name]")
        print("")
        print("Creates sample topics, messages, and consumer groups for testing.")
        print("")
        print("Arguments:")
        print("  cluster_name    Optional cluster name for multi-cluster setups")
        print("")
        print("Environment Variables:")
        print("  KAFKA_BOOTSTRAP_SERVERS - Kafka broker endpoints")
        print("  KAFKA_SECURITY_PROTOCOL - Security protocol")
        print("  KAFKA_SASL_* - SASL authentication parameters")
        return

    # Get cluster name from command line or use default
    cluster_name = sys.argv[1] if len(sys.argv) > 1 else "default"

    # Load configuration
    try:
        from kafka_brokers_unified_mcp import load_cluster_configurations

        manager = load_cluster_configurations()

        if cluster_name == "default" and len(manager.clusters) == 1:
            cluster_name = list(manager.clusters.keys())[0]

        if cluster_name not in manager.clusters:
            print(f"❌ Cluster '{cluster_name}' not found")
            print(f"Available clusters: {list(manager.clusters.keys())}")
            return 1

        cluster_config = manager.get_cluster_config(cluster_name)

    except Exception as e:
        print(f"❌ Failed to load cluster configuration: {e}")
        return 1

    print(f"Using cluster: {cluster_name} ({cluster_config.bootstrap_servers})")

    # Check readonly mode
    if cluster_config.readonly:
        print(f"⚠️  Cluster '{cluster_name}' is in readonly mode!")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            print("Aborted")
            return 0

    # Create Kafka configuration
    kafka_config = {
        "bootstrap.servers": cluster_config.bootstrap_servers,
        "security.protocol": cluster_config.security_protocol,
    }

    if cluster_config.sasl_mechanism:
        kafka_config["sasl.mechanism"] = cluster_config.sasl_mechanism
    if cluster_config.sasl_username:
        kafka_config["sasl.username"] = cluster_config.sasl_username
    if cluster_config.sasl_password:
        kafka_config["sasl.password"] = cluster_config.sasl_password

    try:
        # Create admin client
        admin_client = AdminClient(kafka_config)

        # Test connection
        metadata = admin_client.list_topics(timeout=10)
        print(f"✅ Connected to cluster (found {len(metadata.topics)} existing topics)")

        # Create topics
        created_topics = create_topics(admin_client, cluster_name)

        if not created_topics:
            print("❌ No topics were created")
            return 1

        # Wait for topics to be ready
        print("⏳ Waiting for topics to be ready...")
        time.sleep(5)

        # Produce sample messages
        produce_sample_messages(kafka_config, created_topics)

        # Create consumer groups
        create_consumer_groups(kafka_config, created_topics)

        print("")
        print("🎉 Test data creation completed successfully!")
        print("")
        print("Created:")
        print(f"  📝 {len(created_topics)} topics with sample messages")
        print(f"  👥 5 consumer groups with different consumption patterns")
        print("")
        print("You can now test the MCP server with:")
        print("  python scripts/test_mcp_tools.py")
        print("")
        print("Or use with Claude Desktop to explore:")
        print("  'List all topics in my Kafka cluster'")
        print("  'Show me consumer groups and their status'")
        print("  'Describe the user-events topic'")

        return 0

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
