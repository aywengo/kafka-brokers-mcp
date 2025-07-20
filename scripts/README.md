# Scripts Directory

Utility scripts for testing, development, and maintenance of the Kafka Brokers MCP Server.

## Available Scripts

### test_mcp_tools.py

**Purpose**: Manual testing of MCP tools without requiring Claude Desktop integration.

**Usage**:
```bash
python scripts/test_mcp_tools.py
```

**Features**:
- Tests all MCP tools (list_clusters, list_topics, describe_topic, etc.)
- Works with both single and multi-cluster configurations
- Provides detailed output and error reporting
- Useful for development and debugging
- Validates environment configuration

**Example Output**:
```
============================================================
 Testing Basic MCP Tools
============================================================

Available Clusters:
[
  {
    "name": "development",
    "bootstrap_servers": "localhost:9092",
    "security_protocol": "PLAINTEXT",
    "viewonly": false,
    "topics_count": 8,
    "brokers_count": 1,
    "status": "healthy"
  }
]
```

### create_test_data.py

**Purpose**: Creates sample topics, messages, and consumer groups for testing.

**Usage**:
```bash
# Use default cluster
python scripts/create_test_data.py

# Use specific cluster (multi-cluster setup)
python scripts/create_test_data.py production
```

**Creates**:
- **Topics**: 
  - `user-events` (6 partitions)
  - `order-updates` (3 partitions)
  - `payment-notifications` (2 partitions)
  - `analytics-events` (4 partitions)
  - `system-logs` (8 partitions)

- **Consumer Groups**:
  - `analytics-processor`
  - `order-fulfillment`
  - `payment-processor`
  - `monitoring-service`
  - `data-pipeline`

- **Sample Messages**: Realistic JSON messages for each topic type

**Features**:
- Respects viewonly mode settings
- Configurable partition counts and retention policies
- Produces realistic sample data
- Creates consumer groups with different consumption patterns
- Handles authentication automatically

## Environment Setup

Both scripts use the same environment configuration as the main MCP server:

### Single Cluster
```bash
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export KAFKA_SECURITY_PROTOCOL="PLAINTEXT"
export VIEWONLY="false"
```

### Multi-Cluster
```bash
export KAFKA_CLUSTER_NAME_1="development"
export KAFKA_BOOTSTRAP_SERVERS_1="dev-kafka:9092"
export VIEWONLY_1="false"

export KAFKA_CLUSTER_NAME_2="production"
export KAFKA_BOOTSTRAP_SERVERS_2="prod-kafka:9092"
export KAFKA_SECURITY_PROTOCOL_2="SASL_SSL"
export VIEWONLY_2="true"
```

## Development Workflow

### 1. Setup Test Environment
```bash
# Start test environment
cd tests
./start_test_environment.sh multi
```

### 2. Create Test Data
```bash
# Configure for test environment
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export KAFKA_SECURITY_PROTOCOL="PLAINTEXT"
export VIEWONLY="false"

# Create sample data
python scripts/create_test_data.py
```

### 3. Test MCP Tools
```bash
# Test all MCP functionality
python scripts/test_mcp_tools.py
```

### 4. Test with Claude Desktop
```bash
# Start the MCP server
python kafka_brokers_unified_mcp.py

# Use Claude Desktop to test:
# "List all topics in my Kafka cluster"
# "Show me consumer groups and their lag"
# "Describe the user-events topic"
```

## Common Use Cases

### Development Testing

```bash
# Quick development cycle
./tests/start_test_environment.sh dev
python scripts/create_test_data.py
python scripts/test_mcp_tools.py
```

### Multi-Cluster Testing

```bash
# Test multi-cluster setup
./tests/start_test_environment.sh multi

# Create data in cluster 1
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
python scripts/create_test_data.py

# Create data in cluster 2
export KAFKA_BOOTSTRAP_SERVERS="localhost:9093"
python scripts/create_test_data.py

# Test multi-cluster tools
export KAFKA_CLUSTER_NAME_1="cluster1"
export KAFKA_BOOTSTRAP_SERVERS_1="localhost:9092"
export KAFKA_CLUSTER_NAME_2="cluster2"
export KAFKA_BOOTSTRAP_SERVERS_2="localhost:9093"
python scripts/test_mcp_tools.py
```

### Production Validation

```bash
# Test against production (viewonly)
export KAFKA_BOOTSTRAP_SERVERS="prod-kafka:9092"
export KAFKA_SECURITY_PROTOCOL="SASL_SSL"
export KAFKA_SASL_MECHANISM="SCRAM-SHA-256"
export KAFKA_SASL_USERNAME="viewonly-user"
export KAFKA_SASL_PASSWORD="password"
export VIEWONLY="true"

python scripts/test_mcp_tools.py
```

## Script Options

### test_mcp_tools.py

```bash
# Show help
python scripts/test_mcp_tools.py --help

# Normal execution (tests all functionality)
python scripts/test_mcp_tools.py
```

**Exit Codes**:
- `0`: All tests passed
- `1`: Some tests failed or error occurred

### create_test_data.py

```bash
# Show help
python scripts/create_test_data.py --help

# Create in default cluster
python scripts/create_test_data.py

# Create in specific cluster
python scripts/create_test_data.py staging
```

**Safety Features**:
- Warns if cluster is in viewonly mode
- Checks for existing topics before creation
- Validates cluster connectivity before proceeding

## Troubleshooting

### Connection Issues

```bash
# Test basic connectivity
kafka-topics --bootstrap-server localhost:9092 --list

# Check environment variables
echo $KAFKA_BOOTSTRAP_SERVERS
echo $KAFKA_SECURITY_PROTOCOL
```

### Authentication Issues

```bash
# Verify SASL credentials
echo $KAFKA_SASL_USERNAME
echo $KAFKA_SASL_PASSWORD

# Test authentication
kafka-console-consumer --bootstrap-server localhost:9092 \
  --consumer-property security.protocol=SASL_SSL \
  --consumer-property sasl.mechanism=SCRAM-SHA-256 \
  --topic test-topic --from-beginning --max-messages 1
```

### Permission Issues

```bash
# Check if user has topic creation permissions
kafka-topics --bootstrap-server localhost:9092 \
  --create --topic test-permissions \
  --partitions 1 --replication-factor 1

# Clean up
kafka-topics --bootstrap-server localhost:9092 \
  --delete --topic test-permissions
```

### Script Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python scripts/test_mcp_tools.py

# Python debugging
python -u scripts/test_mcp_tools.py
```

## Integration with Tests

These scripts integrate with the main test suite:

```bash
# Run full test suite (includes script testing)
cd tests
./run_all_tests.sh

# Run specific script tests
python -m pytest test_script_integration.py
```

## Contributing

When adding new scripts:

1. Follow the same configuration patterns
2. Add comprehensive error handling
3. Include help text and usage examples
4. Test with both single and multi-cluster setups
5. Update this README with documentation

## Best Practices

1. **Always test locally first** before running against production
2. **Use viewonly mode** for production environments
3. **Validate environment** configuration before running scripts
4. **Check connectivity** before creating resources
5. **Clean up test data** when no longer needed
6. **Use meaningful names** for test topics and consumer groups
7. **Monitor resource usage** when creating large amounts of test data
