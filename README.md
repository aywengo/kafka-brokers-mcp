# Kafka Brokers MCP Server

A comprehensive Message Control Protocol (MCP) server that provides Claude Desktop and other MCP clients with tools for Kafka broker operations. Features include topic management, consumer group monitoring, broker status checking, and multi-cluster support.

## 🎯 True MCP Implementation

This server uses the official MCP Python SDK and communicates via JSON-RPC over stdio, making it fully compatible with Claude Desktop and other MCP clients.

## ✨ Key Features

- **Claude Desktop Compatible**: Direct integration with Claude Desktop via MCP protocol
- **MCP Tools**: 14 tools for topic operations, consumer group management, and cluster monitoring
- **MCP Resources**: Real-time cluster status, configuration, and cluster-specific resources
- **JSON-RPC Protocol**: Standard MCP communication over stdio
- **Multi-Cluster Support**: Connect to up to 8 Kafka clusters simultaneously
- **Per-Cluster VIEWONLY Mode**: Individual viewonly protection per cluster for production safety
- **Cross-Cluster Operations**: Compare topics and consumer groups between clusters
- **Health Monitoring**: Comprehensive cluster health checks and partition analysis
- **Load Balancing Analysis**: Broker partition distribution and leader analysis
- **Authentication Support**: SASL/SSL authentication for secure Kafka connections
- **confluent-kafka-python**: High-performance Kafka client library

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Latest stable release
docker pull aywengo/kafka-brokers-mcp:stable

# Test with local Kafka
docker run -e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 aywengo/kafka-brokers-mcp:stable
```

### Claude Desktop Integration

Copy a ready-to-use configuration:

```bash
# macOS
cp config-examples/claude_desktop_stable_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linux  
cp config-examples/claude_desktop_stable_config.json ~/.config/claude-desktop/config.json
```

Restart Claude Desktop and start asking about your Kafka clusters!

## 📋 Core MCP Tools

### Topic Management
- `list_topics(cluster?)` - List all topics with metadata (supports optional cluster parameter)
- `describe_topic` - Get detailed topic configuration and partition info
- `get_topic_partition_details` - Get detailed partition info for a topic

### Consumer Group Management
- `list_consumer_groups(cluster?)` - List all consumer groups (supports optional cluster parameter)
- `describe_consumer_group` - Get detailed consumer group info and offsets

### Broker Operations
- `list_brokers(cluster?)` - List all brokers in cluster (supports optional cluster parameter)
- `get_broker_partition_count` - Get partition distribution per broker
- `get_cluster_metadata` - Show cluster-wide information
- `list_clusters` - Show all configured clusters

### Partition Operations
- `get_partitions(cluster?, topic?)` - Get partitions with optional cluster and topic filtering
- `get_partition_leaders` - Get partition leader distribution
- `find_under_replicated_partitions` - Find unhealthy partitions

### Health & Monitoring
- `get_cluster_health` - Get comprehensive cluster health information
- `compare_cluster_topics` - Compare topics between clusters

### MCP Resources
- Global resources: `kafka://brokers`, `kafka://topics`, `kafka://consumer-groups`, `kafka://partitions`
- Cluster-specific resources: `kafka://brokers/{name}`, `kafka://topics/{name}`, etc.
- Cluster status: `kafka://cluster-status`, `kafka://cluster-info`

## 🔧 Configuration

### Single Cluster Mode

```bash
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export KAFKA_SECURITY_PROTOCOL="PLAINTEXT"
export VIEWONLY="false"
```

### Multi-Cluster Mode (Up to 8 clusters)

```bash
# Development cluster
export KAFKA_CLUSTER_NAME_1="development"
export KAFKA_BOOTSTRAP_SERVERS_1="dev-kafka:9092"
export VIEWONLY_1="false"

# Production cluster (with safety)
export KAFKA_CLUSTER_NAME_2="production"  
export KAFKA_BOOTSTRAP_SERVERS_2="prod-kafka:9092"
export KAFKA_SECURITY_PROTOCOL_2="SASL_SSL"
export KAFKA_SASL_MECHANISM_2="SCRAM-SHA-256"
export KAFKA_SASL_USERNAME_2="prod-user"
export KAFKA_SASL_PASSWORD_2="prod-password"
export VIEWONLY_2="true"
```

## 🐳 Development Setup

```bash
git clone https://github.com/aywengo/kafka-brokers-mcp
cd kafka-brokers-mcp
pip install -r requirements.txt
python kafka_brokers_unified_mcp.py
```

### Test Environment

```bash
# Start full test environment
docker-compose up -d

# Run test suite
cd tests
./run_all_tests.sh

# Run specific tests
./run_all_tests.sh --pattern topic
```

## 💬 Example Prompts

Once connected to Claude Desktop:

### Basic Operations
- "List all topics in my Kafka cluster"
- "Show me details about the user-events topic"
- "What consumer groups are active?"
- "Describe the consumer group 'analytics-service'"
- "Show me all brokers in the production cluster"

### Cluster-Specific Operations (NEW)
- "Get brokers for the production cluster using get_brokers with cluster parameter"
- "Show me topics in the development cluster only"
- "Get consumer groups for production cluster using cluster parameter"
- "Get partitions for user-events topic in production cluster"
- "Show me partitions for the production cluster"

### Health & Monitoring (NEW)
- "Check the health of my production cluster"
- "Find any under-replicated partitions in development"
- "Show me partition leader distribution for production"
- "Get broker partition counts to check load balancing"
- "Analyze topic partition details for high-volume-topic"

### Cross-Cluster Operations
- "Compare topics between development and production clusters"
- "Show me brokers across all my clusters"
- "Which consumer groups exist in both environments?"
- "Compare partition counts between dev and prod for user-events topic"

### Resource-Based Operations
- "Access the kafka://cluster-health/production resource"
- "Get data from kafka://brokers/development"
- "Show me the kafka://topics/production resource"

## 🔒 VIEWONLY Mode

When `VIEWONLY=true` is set, the MCP server blocks all modification operations:

**Blocked Operations:**
- ❌ Topic creation and deletion
- ❌ Configuration changes
- ❌ Consumer group offset resets

**Allowed Operations:**
- ✅ Topic and broker browsing
- ✅ Consumer group monitoring
- ✅ Cluster metadata retrieval
- ✅ Configuration reading

## 🛠 Advanced Features

### Authentication Support
- SASL/PLAIN, SASL/SCRAM-SHA-256, SASL/SCRAM-SHA-512
- SSL/TLS encryption
- Multiple authentication methods per cluster

### Multi-Cluster Operations
- Cross-cluster topic comparison
- Consumer group analysis across environments
- Cluster health monitoring

### Real-time Resources

#### Global Resources
- `kafka://cluster-status` - Live cluster status across all clusters
- `kafka://cluster-info` - Detailed configuration for all clusters
- `kafka://brokers` - All brokers across clusters
- `kafka://topics` - All topics across clusters
- `kafka://consumer-groups` - All consumer groups across clusters
- `kafka://partitions` - All partitions across clusters

#### Cluster-Specific Resources (NEW)
- `kafka://brokers/{name}` - Brokers for a specific cluster
- `kafka://topics/{name}` - Topics for a specific cluster
- `kafka://consumer-groups/{name}` - Consumer groups for a specific cluster
- `kafka://partitions/{name}` - Partitions for a specific cluster
- `kafka://cluster-health/{name}` - Health metrics for a specific cluster

## 📊 Monitoring

Access Kafka UI for visual monitoring:
```bash
docker-compose up kafka-ui
# Visit http://localhost:8080
```

## 🤝 Contributing

Following the same patterns as the kafka-schema-reg-mcp project:

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `./tests/run_all_tests.sh`
5. Update the README.md file with the new functionality.
6. Fix formatting with `black` and `isort`.
7. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Related Projects

- [kafka-schema-reg-mcp](https://github.com/aywengo/kafka-schema-reg-mcp) - MCP server for Kafka Schema Registry operations
- [Apache Kafka](https://kafka.apache.org/) - Distributed streaming platform
- [confluent-kafka-python](https://github.com/confluentinc/confluent-kafka-python) - Kafka Python client
