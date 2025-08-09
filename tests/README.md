# Testing Guide

This directory contains comprehensive testing infrastructure for the Kafka Brokers MCP Server. The setup includes multi-cluster Kafka environments and AKHQ UI monitoring for development and testing.

## Quick Start

### Start Test Environment

```bash
# Single cluster mode (for basic testing)
./start_test_environment.sh dev

# Multi-cluster mode (for cluster comparison features)
./start_test_environment.sh multi

# UI mode (includes AKHQ web interface)
./start_test_environment.sh ui
```

### Access MCP Inspector

The test environment includes an HTTP-enabled MCP server for interactive testing. You can use either the CLI Inspector or the MCPJam Inspector (web UI):

```bash
# Tip: 404 on GET / at http://localhost:8000 is expected; MCP uses POST endpoints.
```

**MCP Inspector Features:**
- 🔧 **Tools Testing**: Execute MCP tools with custom parameters
- 📋 **Resources Exploration**: Browse available resources and their content
- 💬 **Prompts Testing**: Test prompt templates with different arguments
- 📊 **Real-time Monitoring**: View server logs and notifications
- 🔍 **Schema Inspection**: Examine tool schemas and resource metadata

### Stop Environment

```bash
./stop_test_environment.sh
```

## Environment Details

### Available Services

| Service | Purpose | Access |
|---------|---------|--------|
| **kafka-dev** | Development Kafka cluster | localhost:9092 |
| **kafka-prod** | Production Kafka cluster | localhost:39093 |
| **kafka-mcp-server** | MCP server (stdio transport) | Docker container |
| **kafka-mcp-server-http** | MCP server (HTTP transport) | http://localhost:8000 |
| **akhq** | Kafka UI dashboard | http://localhost:38080 |
|  |  |  |

### MCP Server Access

The test environment provides two MCP server instances:

1. **Stdio Transport** (`kafka-mcp-server`): For Claude Desktop integration
2. **HTTP Transport** (`kafka-mcp-server-http`): For HTTP-based clients

Both servers connect to the same Kafka clusters and provide identical functionality.

## Testing Workflows

### 1. Interactive Development

```bash
# Start environment with UI
./start_test_environment.sh ui

# Monitor Kafka with AKHQ
open http://localhost:38080
```

### 2. Automated Testing

```bash
# Run all test suites
./run_all_tests.sh

# Run specific test category
python run_single_test.py test_topic_operations.py
```

### 3. Multi-Cluster Testing

```bash
# Start multi-cluster environment
./start_test_environment.sh multi

# Test cross-cluster operations in MCP Inspector:
# - compare_cluster_topics
# - list_topics (with cluster parameter)
# - Cross-cluster consumer group analysis
```

## Development Tips

### Using MCP Inspector

1. **Tool Exploration**: Browse all available tools and their schemas
2. **Parameter Testing**: Test edge cases with different parameter combinations
3. **Error Handling**: Verify error responses and validation
4. **Performance**: Monitor execution times for different operations
5. **Multi-cluster**: Test cluster-specific operations

### Common MCP Inspector Operations

```javascript
// List all available tools
await client.list_tools()

// Test topic listing for specific cluster
await client.call_tool("list_topics", {"cluster": "dev"})

// Compare topics between clusters
await client.call_tool("compare_cluster_topics", {
  "cluster1": "dev", 
  "cluster2": "prod"
})

// Get detailed cluster health
await client.call_tool("get_cluster_health", {"cluster": "dev"})
```

### Troubleshooting

#### MCP Inspector Connection Issues

```bash
# Check if HTTP MCP server is running
curl http://localhost:8000/

# View HTTP MCP server logs
docker compose -f docker-compose.yml logs -f kafka-mcp-server-http

# Restart HTTP MCP server only
docker compose -f docker-compose.yml restart kafka-mcp-server-http
```

 

#### Kafka Connection Issues

```bash
# Check Kafka cluster health
docker compose -f docker-compose.yml exec kafka-dev kafka-topics --bootstrap-server localhost:9092 --list

# View Kafka logs
docker compose -f docker-compose.yml logs -f kafka-dev
```

## Advanced Configuration

### Custom Kafka Configuration

Modify `docker-compose.yml` to adjust:
- Kafka broker settings
- Security protocols  
- Network configuration
- Resource limits

### MCP Server Configuration

Environment variables for MCP server customization:
- `KAFKA_CLUSTERS`: Multi-cluster JSON configuration
- `VIEWONLY`: Enable read-only mode
- `MCP_TRANSPORT`: Transport type (stdio/http)
- `MCP_SERVER_HOST`: HTTP server host
- `MCP_SERVER_PORT`: HTTP server port

## Integration Testing

### Claude Desktop Integration

```json
// Add to claude_desktop_config.json
{
  "mcpServers": {
    "kafka-brokers": {
      "command": "docker",
      "args": ["exec", "-i", "kafka-mcp-server", "python", "kafka_brokers_unified_mcp.py"],
      "env": {
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092"
      }
    }
  }
}
```

### API Integration

```python
from fastmcp import Client

# Connect to HTTP MCP server
client = Client("http://localhost:8000")

async with client:
    tools = await client.list_tools()
    result = await client.call_tool("list_topics", {})
```

## Contributing

When developing new features:

1. **Start with MCP Inspector**: Test new tools interactively
2. **Add automated tests**: Create test cases in `test_*.py` files  
3. **Update documentation**: Document new tools and resources
4. **Test multi-cluster**: Verify functionality across different cluster configurations

For questions or issues, check the logs and use the MCP Inspector for debugging! 