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
