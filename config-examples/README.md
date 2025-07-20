# Configuration Examples

This directory contains pre-configured Claude Desktop configuration examples for different use cases.

## Available Configurations

### Production Use

**`claude_desktop_stable_config.json`**
- Uses stable Docker image from Docker Hub
- Single cluster configuration
- Ready for production use
- Recommended for most users

### Multi-Cluster Management

**`claude_desktop_multi_cluster_config.json`**
- Supports multiple Kafka clusters (development + production)
- Per-cluster viewonly protection
- Different authentication methods per cluster
- Perfect for DevOps teams

### Local Development

**`claude_desktop_local_dev_config.json`**
- Runs Python directly (no Docker)
- Fastest for development and testing
- Requires local Python environment
- Good for contributors

## Installation

### macOS
```bash
cp claude_desktop_stable_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Linux
```bash
cp claude_desktop_stable_config.json ~/.config/claude-desktop/config.json
```

### Windows
```cmd
copy claude_desktop_stable_config.json %APPDATA%\Claude\claude_desktop_config.json
```

## Configuration Variables

### Single Cluster Mode

| Variable | Description | Default | Example |
|----------|-------------|---------|----------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker endpoints | `localhost:9092` | `kafka1:9092,kafka2:9092` |
| `KAFKA_SECURITY_PROTOCOL` | Security protocol | `PLAINTEXT` | `SASL_SSL` |
| `KAFKA_SASL_MECHANISM` | SASL mechanism | (empty) | `SCRAM-SHA-256` |
| `KAFKA_SASL_USERNAME` | SASL username | (empty) | `kafka-user` |
| `KAFKA_SASL_PASSWORD` | SASL password | (empty) | `secret-password` |
| `VIEWONLY` | Enable viewonly mode | `false` | `true` |

### Multi-Cluster Mode

| Variable | Description | Example |
|----------|-------------|----------|
| `KAFKA_CLUSTER_NAME_X` | Cluster name (X=1-8) | `production` |
| `KAFKA_BOOTSTRAP_SERVERS_X` | Cluster endpoints | `prod-kafka:9092` |
| `KAFKA_SECURITY_PROTOCOL_X` | Security protocol | `SASL_SSL` |
| `KAFKA_SASL_MECHANISM_X` | SASL mechanism | `SCRAM-SHA-256` |
| `KAFKA_SASL_USERNAME_X` | SASL username | `prod-user` |
| `KAFKA_SASL_PASSWORD_X` | SASL password | `prod-password` |
| `VIEWONLY_X` | Per-cluster viewonly | `true` |

## Security Best Practices

### Production Environment
- Always use `VIEWONLY=true` for production clusters
- Use strong authentication (SASL/SSL)
- Store credentials securely
- Regularly rotate passwords

### Development Environment
- Use separate dev clusters
- Enable full access (`VIEWONLY=false`)
- Use simple authentication for testing

## Troubleshooting

### Connection Issues
1. Verify broker endpoints are accessible
2. Check authentication credentials
3. Confirm security protocol settings
4. Test network connectivity

### Configuration Issues
1. Validate JSON syntax
2. Check environment variable names
3. Verify file permissions
4. Restart Claude Desktop after changes

### Common Errors

**"No cluster configurations found"**
- Check environment variables are set
- Verify variable naming (KAFKA_BOOTSTRAP_SERVERS vs KAFKA_BOOTSTRAP_SERVERS_1)

**"Authentication failed"**
- Verify username/password
- Check SASL mechanism
- Confirm SSL certificates

**"Connection timeout"**
- Check network connectivity
- Verify broker addresses
- Test firewall settings

## Example Prompts

Once configured, try these prompts in Claude Desktop:

### Single Cluster
- "List all topics in my Kafka cluster"
- "Show me details about the user-events topic"
- "What consumer groups are active?"
- "Describe the consumer group 'analytics-service'"

### Multi-Cluster
- "List all my Kafka clusters"
- "Show topics in the production cluster"
- "Compare development and production clusters"
- "Show consumer groups in dev vs prod"

## Support

For additional help:
- Check the main [README.md](../README.md)
- Review [troubleshooting guide](../docs/troubleshooting.md)
- Open an issue on GitHub
- Join the community discussions
