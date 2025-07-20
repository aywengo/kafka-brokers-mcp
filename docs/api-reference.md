# API Reference

Complete reference for all MCP tools and resources provided by the Kafka Brokers MCP Server.

## MCP Resources

### kafka://cluster-status

Provides real-time cluster status information.

**Returns:** JSON string with cluster health and metrics

```json
{
  "clusters": {
    "default": {
      "name": "default",
      "bootstrap_servers": "localhost:9092",
      "viewonly": false,
      "topics_count": 5,
      "brokers_count": 1,
      "status": "healthy"
    }
  },
  "timestamp": 1704067200.0
}
```

### kafka://cluster-info

Provides detailed cluster configuration information.

**Returns:** JSON string with server and cluster configuration

```json
{
  "server_version": "1.0.0",
  "clusters": {
    "default": {
      "name": "default",
      "bootstrap_servers": "localhost:9092",
      "security_protocol": "PLAINTEXT",
      "viewonly": false,
      "authentication": {
        "sasl_mechanism": null,
        "has_credentials": false
      }
    }
  },
  "configuration": {
    "viewonly_protection": false,
    "multi_cluster_mode": false,
    "total_clusters": 1
  }
}
```

### kafka://brokers

Provides real-time broker information across all clusters.

**Returns:** JSON string with broker details for all clusters

```json
{
  "brokers": {
    "default": [
      {
        "broker_id": 1,
        "host": "localhost",
        "port": 9092,
        "rack": null,
        "cluster": "default"
      }
    ]
  },
  "timestamp": 1704067200.0
}
```

### kafka://topics

Provides real-time topic information across all clusters.

**Returns:** JSON string with topic details for all clusters

```json
{
  "topics": {
    "default": [
      {
        "name": "user-events",
        "partitions": 6,
        "replication_factor": 3,
        "internal": false,
        "cluster": "default"
      }
    ]
  },
  "timestamp": 1704067200.0
}
```

### kafka://consumer-groups

Provides real-time consumer group information across all clusters.

**Returns:** JSON string with consumer group details for all clusters

```json
{
  "consumer_groups": {
    "default": [
      {
        "group_id": "analytics-service",
        "is_simple_consumer_group": false,
        "state": "STABLE",
        "cluster": "default"
      }
    ]
  },
  "timestamp": 1704067200.0
}
```

### kafka://partitions

Provides real-time partition information across all clusters.

**Returns:** JSON string with partition details for all clusters

```json
{
  "partitions": {
    "default": [
      {
        "topic": "user-events",
        "partition_id": 0,
        "leader": 1,
        "replicas": [1, 2, 3],
        "in_sync_replicas": [1, 2, 3],
        "error": null,
        "cluster": "default"
      }
    ]
  },
  "timestamp": 1704067200.0
}
```

### kafka://brokers/{name}

Provides real-time broker information for a specific cluster.

**Parameters:**
- `name`: Cluster name

**Returns:** JSON string with broker details for the specified cluster

```json
{
  "cluster": "production",
  "brokers": [
    {
      "broker_id": 1,
      "host": "prod-kafka-1",
      "port": 9092,
      "rack": "rack-1",
      "cluster": "production"
    }
  ],
  "timestamp": 1704067200.0
}
```

### kafka://topics/{name}

Provides real-time topic information for a specific cluster.

**Parameters:**
- `name`: Cluster name

**Returns:** JSON string with topic details for the specified cluster

```json
{
  "cluster": "production",
  "topics": [
    {
      "name": "user-events",
      "partitions": 6,
      "replication_factor": 3,
      "internal": false,
      "cluster": "production"
    }
  ],
  "timestamp": 1704067200.0
}
```

### kafka://consumer-groups/{name}

Provides real-time consumer group information for a specific cluster.

**Parameters:**
- `name`: Cluster name

**Returns:** JSON string with consumer group details for the specified cluster

```json
{
  "cluster": "production",
  "consumer_groups": [
    {
      "group_id": "analytics-service",
      "is_simple_consumer_group": false,
      "state": "STABLE",
      "cluster": "production"
    }
  ],
  "timestamp": 1704067200.0
}
```

### kafka://partitions/{name}

Provides real-time partition information for a specific cluster.

**Parameters:**
- `name`: Cluster name

**Returns:** JSON string with partition details for the specified cluster

```json
{
  "cluster": "production",
  "partitions": [
    {
      "topic": "user-events",
      "partition_id": 0,
      "leader": 1,
      "replicas": [1, 2, 3],
      "in_sync_replicas": [1, 2, 3],
      "error": null,
      "cluster": "production"
    }
  ],
  "timestamp": 1704067200.0
}
```

### kafka://cluster-health/{name}

Provides comprehensive health information for a specific cluster.

**Parameters:**
- `name`: Cluster name

**Returns:** JSON string with health metrics for the specified cluster

```json
{
  "cluster": "production",
  "health_status": "healthy",
  "cluster_info": {
    "cluster_id": "kafka-cluster-prod",
    "controller_id": 1,
    "bootstrap_servers": "prod-kafka:9092",
    "viewonly": true
  },
  "metrics": {
    "broker_count": 3,
    "topic_count": 15,
    "partition_count": 120,
    "unhealthy_partitions": 0,
    "health_percentage": 100.0
  },
  "timestamp": 1704067200.0
}
```

## MCP Tools

### list_clusters()

Lists all configured Kafka clusters with their status.

**Parameters:** None

**Returns:** `List[Dict[str, Any]]`

**Example:**
```python
[
  {
    "name": "development",
    "bootstrap_servers": "localhost:9092",
    "security_protocol": "PLAINTEXT",
    "viewonly": false,
    "topics_count": 3,
    "brokers_count": 1,
    "status": "healthy"
  },
  {
    "name": "production",
    "bootstrap_servers": "prod-kafka:9092",
    "security_protocol": "SASL_SSL",
    "viewonly": true,
    "topics_count": 15,
    "brokers_count": 3,
    "status": "healthy"
  }
]
```

### list_topics(cluster: Optional[str] = None)

Lists all topics in the specified cluster (excluding internal topics).

**Parameters:**
- `cluster` (optional): Cluster name. If not specified, uses default cluster.

**Returns:** `List[Dict[str, Any]]`

**Example:**
```python
[
  {
    "name": "user-events",
    "partitions": 6,
    "replication_factor": 3,
    "internal": false
  },
  {
    "name": "order-updates",
    "partitions": 3,
    "replication_factor": 2,
    "internal": false
  }
]
```

### describe_topic(topic_name: str, cluster: Optional[str] = None)

Provides detailed information about a specific topic.

**Parameters:**
- `topic_name`: Name of the topic to describe
- `cluster` (optional): Cluster name

**Returns:** `Dict[str, Any]`

**Example:**
```python
{
  "name": "user-events",
  "partitions": [
    {
      "partition_id": 0,
      "leader": 1,
      "replicas": [1, 2, 3],
      "in_sync_replicas": [1, 2, 3],
      "error": null
    },
    {
      "partition_id": 1,
      "leader": 2,
      "replicas": [2, 3, 1],
      "in_sync_replicas": [2, 3, 1],
      "error": null
    }
  ],
  "partition_count": 6,
  "replication_factor": 3,
  "configurations": {
    "cleanup.policy": "delete",
    "retention.ms": "604800000",
    "segment.ms": "604800000"
  },
  "internal": false
}
```

### list_consumer_groups(cluster: Optional[str] = None)

Lists all consumer groups in the specified cluster.

**Parameters:**
- `cluster` (optional): Cluster name

**Returns:** `List[Dict[str, Any]]`

**Example:**
```python
[
  {
    "group_id": "analytics-service",
    "is_simple_consumer_group": false,
    "state": "Stable"
  },
  {
    "group_id": "user-processor",
    "is_simple_consumer_group": false,
    "state": "Stable"
  }
]
```

### describe_consumer_group(group_id: str, cluster: Optional[str] = None)

Provides detailed information about a specific consumer group.

**Parameters:**
- `group_id`: Consumer group ID to describe
- `cluster` (optional): Cluster name

**Returns:** `Dict[str, Any]`

**Example:**
```python
{
  "group_id": "analytics-service",
  "state": "Stable",
  "protocol_type": "consumer",
  "protocol": "range",
  "coordinator": {
    "id": 1,
    "host": "kafka-broker-1",
    "port": 9092
  },
  "members": [
    {
      "member_id": "consumer-1-12345",
      "client_id": "analytics-consumer",
      "client_host": "/192.168.1.100",
      "assignments": [
        {
          "topic": "user-events",
          "partition": 0
        },
        {
          "topic": "user-events",
          "partition": 1
        }
      ]
    }
  ],
  "member_count": 1,
  "offsets": [
    {
      "topic": "user-events",
      "partition": 0,
      "current_offset": 1523,
      "metadata": ""
    }
  ]
}
```

### list_brokers(cluster: Optional[str] = None)

Lists all brokers in the specified cluster.

**Parameters:**
- `cluster` (optional): Cluster name

**Returns:** `List[Dict[str, Any]]`

**Example:**
```python
[
  {
    "broker_id": 1,
    "host": "kafka-broker-1",
    "port": 9092,
    "rack": "rack-1"
  },
  {
    "broker_id": 2,
    "host": "kafka-broker-2", 
    "port": 9092,
    "rack": "rack-2"
  }
]
```

### get_cluster_metadata(cluster: Optional[str] = None)

Provides comprehensive cluster metadata and statistics.

**Parameters:**
- `cluster` (optional): Cluster name

**Returns:** `Dict[str, Any]`

**Example:**
```python
{
  "cluster_name": "production",
  "bootstrap_servers": "prod-kafka:9092",
          "viewonly": true,
  "cluster_id": "kafka-cluster-prod",
  "controller_id": 1,
  "brokers": {
    "count": 3,
    "ids": [1, 2, 3]
  },
  "topics": {
    "total": 25,
    "user_topics": 15,
    "internal_topics": 10,
    "total_partitions": 120
  },
  "security": {
    "protocol": "SASL_SSL",
    "sasl_mechanism": "SCRAM-SHA-256",
    "authentication_enabled": true
  }
}
```







### get_partitions(cluster: Optional[str] = None, topic: Optional[str] = None)

Get partitions from kafka://partitions resource or cluster-specific resource.

**Parameters:**
- `cluster` (optional): Cluster name. If specified, uses cluster-specific resource. If not specified, returns partitions from all clusters.
- `topic` (optional): Topic name. If specified, returns only partitions for that topic.

**Returns:** `List[Dict[str, Any]]`

**Example:**
```python
# All clusters, all topics
[
  {
    "topic": "user-events",
    "partition_id": 0,
    "leader": 1,
    "replicas": [1, 2, 3],
    "in_sync_replicas": [1, 2, 3],
    "error": null,
    "cluster": "default"
  },
  {
    "topic": "user-events",
    "partition_id": 1,
    "leader": 2,
    "replicas": [2, 3, 1],
    "in_sync_replicas": [2, 3, 1],
    "error": null,
    "cluster": "production"
  }
]

# Specific cluster and topic: get_partitions(cluster="production", topic="user-events")
[
  {
    "topic": "user-events",
    "partition_id": 1,
    "leader": 2,
    "replicas": [2, 3, 1],
    "in_sync_replicas": [2, 3, 1],
    "error": null,
    "cluster": "production"
  }
]
```

### get_cluster_health(cluster: str)

Get comprehensive health information for a specific cluster.

**Parameters:**
- `cluster`: Name of the cluster

**Returns:** `Dict[str, Any]`

**Example:**
```python
{
  "cluster": "production",
  "health_status": "healthy",
  "cluster_info": {
    "cluster_id": "kafka-cluster-prod",
    "controller_id": 1,
    "bootstrap_servers": "prod-kafka:9092",
    "viewonly": true
  },
  "metrics": {
    "broker_count": 3,
    "topic_count": 15,
    "partition_count": 120,
    "unhealthy_partitions": 0,
    "health_percentage": 100.0
  }
}
```

### compare_cluster_topics(source_cluster: str, target_cluster: str)

Compare topics between two clusters.

**Parameters:**
- `source_cluster`: Name of the source cluster
- `target_cluster`: Name of the target cluster

**Returns:** `Dict[str, Any]`

**Example:**
```python
{
  "source_cluster": "development",
  "target_cluster": "production",
  "summary": {
    "total_source_topics": 5,
    "total_target_topics": 15,
    "common_topics": 5,
    "only_in_source": 0,
    "only_in_target": 10,
    "topics_with_differences": 2
  },
  "only_in_source": [],
  "only_in_target": ["prod-only-topic"],
  "topic_differences": [
    {
      "topic": "user-events",
      "differences": {
        "partitions": {"source": 3, "target": 6}
      }
    }
  ]
}
```

### get_partition_leaders(cluster_name: str)

Get partition leader distribution across brokers for a cluster.

**Parameters:**
- `cluster_name`: Name of the cluster

**Returns:** `Dict[str, Any]`

**Example:**
```python
{
  "cluster": "production",
  "total_partitions": 120,
  "total_brokers": 3,
  "leader_distribution": [
    {
      "broker_id": 1,
      "host": "kafka-1",
      "port": 9092,
      "partition_count": 40,
      "topics": {"user-events": 6, "orders": 3}
    }
  ],
  "balance_ratio": 0.95
}
```

### get_topic_partition_details(cluster_name: str, topic_name: str)

Get detailed partition information for a specific topic.

**Parameters:**
- `cluster_name`: Name of the cluster
- `topic_name`: Name of the topic

**Returns:** `Dict[str, Any]`

**Example:**
```python
{
  "cluster": "production",
  "topic": "user-events",
  "partition_count": 6,
  "replication_factor": 3,
  "health": {
    "healthy_partitions": 6,
    "unhealthy_partitions": 0,
    "health_percentage": 100.0
  },
  "partitions": [
    {
      "partition_id": 0,
      "leader": {
        "broker_id": 1,
        "host": "kafka-1",
        "port": 9092
      },
      "replicas": [
        {
          "broker_id": 1,
          "host": "kafka-1",
          "port": 9092,
          "in_sync": true
        }
      ],
      "is_healthy": true
    }
  ]
}
```

### find_under_replicated_partitions(cluster_name: str)

Find partitions that are under-replicated (fewer ISRs than replicas).

**Parameters:**
- `cluster_name`: Name of the cluster

**Returns:** `List[Dict[str, Any]]`

**Example:**
```python
[
  {
    "topic": "user-events",
    "partition_id": 2,
    "leader": 1,
    "replicas": [1, 2, 3],
    "in_sync_replicas": [1, 3],
    "missing_replicas": 1,
    "replication_factor": 3,
    "cluster": "production"
  }
]
```

### get_broker_partition_count(cluster_name: str)

Get partition count per broker for load balancing analysis.

**Parameters:**
- `cluster_name`: Name of the cluster

**Returns:** `List[Dict[str, Any]]`

**Example:**
```python
[
  {
    "broker_id": 1,
    "host": "kafka-1",
    "port": 9092,
    "leader_count": 40,
    "replica_count": 120,
    "topic_count": 15
  }
]
```

## Error Handling

All tools follow consistent error handling patterns:

### Common Errors

**ValueError**: Raised for invalid parameters or missing resources
```python
# Examples:
raise ValueError("Topic 'nonexistent-topic' not found")
raise ValueError("Cluster 'invalid-cluster' not found")
raise ValueError("Consumer group 'missing-group' not found")
```

**Connection Errors**: Raised when cluster is unreachable
```python
# Logged as warnings and returned in status responses
{
  "name": "production",
  "status": "error",
  "error": "Failed to connect to broker: Connection refused"
}
```

### Viewonly Mode Protection

When a cluster is in viewonly mode, certain operations are blocked:

**Blocked Operations:**
- Topic creation/deletion
- Configuration modifications
- Consumer group offset resets

**Allowed Operations:**
- All read operations (list, describe, get)
- Status and metadata queries
- Configuration reading

## Authentication

The server supports various Kafka authentication mechanisms:

### SASL/PLAIN
```bash
export KAFKA_SECURITY_PROTOCOL="SASL_PLAINTEXT"
export KAFKA_SASL_MECHANISM="PLAIN"
export KAFKA_SASL_USERNAME="kafka-user"
export KAFKA_SASL_PASSWORD="kafka-password"
```

### SASL/SCRAM-SHA-256
```bash
export KAFKA_SECURITY_PROTOCOL="SASL_SSL"
export KAFKA_SASL_MECHANISM="SCRAM-SHA-256"
export KAFKA_SASL_USERNAME="kafka-user"
export KAFKA_SASL_PASSWORD="kafka-password"
```

### SSL
```bash
export KAFKA_SECURITY_PROTOCOL="SSL"
export KAFKA_SSL_CA_LOCATION="/path/to/ca-cert"
export KAFKA_SSL_CERTIFICATE_LOCATION="/path/to/client-cert"
export KAFKA_SSL_KEY_LOCATION="/path/to/client-key"
```

## Multi-Cluster Configuration

Supports up to 8 clusters with independent configurations:

```bash
# Cluster 1 - Development
export KAFKA_CLUSTER_NAME_1="development"
export KAFKA_BOOTSTRAP_SERVERS_1="dev-kafka:9092"
export KAFKA_SECURITY_PROTOCOL_1="PLAINTEXT"
export VIEWONLY_1="false"

# Cluster 2 - Production
export KAFKA_CLUSTER_NAME_2="production"
export KAFKA_BOOTSTRAP_SERVERS_2="prod-kafka:9092"
export KAFKA_SECURITY_PROTOCOL_2="SASL_SSL"
export KAFKA_SASL_MECHANISM_2="SCRAM-SHA-256"
export KAFKA_SASL_USERNAME_2="prod-user"
export KAFKA_SASL_PASSWORD_2="prod-password"
export VIEWONLY_2="true"
```

## Performance Considerations

### Async Operations
All MCP tools use async/await patterns with ThreadPoolExecutor for non-blocking Kafka operations.

### Connection Pooling
Admin clients are cached and reused across tool calls for better performance.

### Timeouts
All Kafka operations include configurable timeouts (default: 10 seconds).

### Resource Limits
ThreadPoolExecutor limited to 10 concurrent workers to prevent resource exhaustion.
