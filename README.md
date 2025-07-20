# Kafka Brokers MCP Server

A comprehensive Message Control Protocol (MCP) server that provides Claude Desktop and other MCP clients with tools for Kafka broker operations. Features include topic management, consumer group monitoring, broker status checking, and multi-cluster support.

## 🎯 True MCP Implementation

This server uses the official MCP Python SDK and communicates via JSON-RPC over stdio, making it fully compatible with Claude Desktop and other MCP clients.

## ✨ Key Features

- **Claude Desktop Compatible**: Direct integration with Claude Desktop via MCP protocol
- **MCP Tools**: 15+ tools for topic operations, consumer group management, and cluster monitoring
- **MCP Resources**: Real-time cluster status and configuration information
- **JSON-RPC Protocol**: Standard MCP communication over stdio
- **Multi-Cluster Support**: Connect to up to 8 Kafka clusters simultaneously
- **Per-Cluster VIEWONLY Mode**: Individual viewonly protection per cluster for production safety
- **Cross-Cluster Operations**: Compare topics and consumer groups between clusters
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
- `list_topics` - List all topics with metadata
- `describe_topic` - Get detailed topic configuration and partition info
- `create_topic` - Create new topics (if not viewonly)
- `delete_topic` - Delete topics (if not viewonly)

### Consumer Group Management
- `list_consumer_groups` - List all consumer groups
- `describe_consumer_group` - Get detailed consumer group info and offsets
- `get_consumer_group_offsets` - Show current offsets and lag

### Broker Operations
- `list_brokers` - List all brokers in cluster
- `describe_broker` - Get broker details and configurations
- `get_cluster_metadata` - Show cluster-wide information
- `list_clusters` - Show all configured clusters

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

- "List all topics in my Kafka cluster"
- "Show me details about the user-events topic"
- "What consumer groups are active?"
- "Describe the consumer group 'analytics-service'"
- "Show me all brokers in the production cluster"
- "Compare topics between development and production clusters"

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
- `kafka://cluster-status` - Live cluster status
- `kafka://cluster-info` - Detailed configuration

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
