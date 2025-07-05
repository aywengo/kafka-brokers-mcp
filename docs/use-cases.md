# Use Cases and Examples

Comprehensive guide showing practical applications of the Kafka Brokers MCP Server in real-world scenarios.

## Overview

The Kafka Brokers MCP Server enables natural language interaction with Kafka clusters through Claude Desktop, making complex Kafka operations accessible to both technical and non-technical users.

## Primary Use Cases

### 1. DevOps and Operations

#### Cluster Health Monitoring
**Scenario**: Operations team needs to quickly check the health of multiple Kafka clusters.

**Claude Prompts**:
- "Show me the status of all Kafka clusters"
- "Are there any unhealthy brokers in production?"
- "What's the current state of consumer groups?"
- "How many topics are in each cluster?"

**Benefits**:
- Quick health assessments without command-line tools
- Multi-cluster visibility in a single interface
- Immediate alerts about issues

#### Capacity Planning
**Scenario**: Planning resource allocation and scaling decisions.

**Claude Prompts**:
- "Show me partition distribution across topics"
- "Which topics have the most partitions?"
- "What's the replication factor for critical topics?"
- "Compare broker utilization across clusters"

**Implementation**:
```bash
# Multi-cluster setup for ops team
export KAFKA_CLUSTER_NAME_1="development"
export KAFKA_BOOTSTRAP_SERVERS_1="dev-kafka:9092"
export READONLY_1="false"

export KAFKA_CLUSTER_NAME_2="staging"
export KAFKA_BOOTSTRAP_SERVERS_2="staging-kafka:9092" 
export READONLY_2="false"

export KAFKA_CLUSTER_NAME_3="production"
export KAFKA_BOOTSTRAP_SERVERS_3="prod-kafka:9092"
export KAFKA_SECURITY_PROTOCOL_3="SASL_SSL"
export READONLY_3="true"  # Production safety
```

### 2. Development and Debugging

#### Application Development
**Scenario**: Developers building Kafka-based applications need to understand topic structure and consumer behavior.

**Claude Prompts**:
- "What topics are available for the user service?"
- "Show me the schema and partitions for user-events topic"
- "Is my consumer group 'analytics-processor' consuming messages?"
- "What's the lag for my consumer group?"

#### Troubleshooting Consumer Issues
**Scenario**: Debugging why a consumer application isn't processing messages.

**Claude Prompts**:
- "Describe the consumer group 'payment-processor'"
- "Show me the current offsets for each partition"
- "Are there any stuck consumers?"
- "Which partitions are assigned to each consumer?"

**Example Response**:
```json
{
  "group_id": "payment-processor",
  "state": "Stable",
  "member_count": 3,
  "offsets": [
    {
      "topic": "payment-events",
      "partition": 0,
      "current_offset": 1523,
      "high_watermark": 1525,
      "lag": 2
    }
  ]
}
```

### 3. Data Engineering

#### Stream Processing Pipeline Management
**Scenario**: Data engineers managing complex streaming pipelines with multiple topics and consumers.

**Claude Prompts**:
- "List all topics related to user data processing"
- "Show me the consumer groups processing clickstream data"
- "What's the throughput for each partition in the events topic?"
- "Are there any consumer groups with high lag?"

#### Data Pipeline Monitoring
**Scenario**: Ensuring data flows correctly through streaming pipelines.

**Claude Prompts**:
- "Show me all consumer groups and their current state"
- "Which topics have messages waiting to be processed?"
- "Compare message production vs consumption rates"

### 4. Team Collaboration

#### Cross-Team Communication
**Scenario**: Product managers and analysts need access to Kafka information without technical complexity.

**Claude Prompts**:
- "What data streams are available for analytics?"
- "Show me topics related to user behavior tracking"
- "How many different data sources are feeding into Kafka?"
- "What consumer applications are processing user data?"

#### Knowledge Sharing
**Scenario**: Onboarding new team members or sharing Kafka knowledge.

**Claude Prompts**:
- "Explain the structure of our payment processing topics"
- "What consumer groups are used by the recommendation service?"
- "Show me how data flows through our event streaming system"

## Industry-Specific Examples

### E-Commerce Platform

#### Order Processing Monitoring
```bash
# Configuration for e-commerce platform
export KAFKA_CLUSTER_NAME_1="orders-cluster"
export KAFKA_BOOTSTRAP_SERVERS_1="orders-kafka:9092"

export KAFKA_CLUSTER_NAME_2="analytics-cluster"
export KAFKA_BOOTSTRAP_SERVERS_2="analytics-kafka:9092"
```

**Common Prompts**:
- "Show me all order-related topics"
- "Is the payment processing consumer group healthy?"
- "What's the current order volume based on topic activity?"
- "Are there any stuck orders in the processing pipeline?"

#### Inventory Management
**Claude Prompts**:
- "Show me inventory update topics and their consumers"
- "Which consumer groups are processing stock level changes?"
- "What's the latency for inventory updates?"

### Financial Services

#### Transaction Processing
```bash
# High-security configuration
export KAFKA_SECURITY_PROTOCOL="SASL_SSL"
export KAFKA_SASL_MECHANISM="SCRAM-SHA-256"
export READONLY="true"  # Read-only for compliance
```

**Common Prompts**:
- "Show me transaction processing topics"
- "Are fraud detection consumers keeping up with transaction volume?"
- "What's the status of payment settlement pipelines?"
- "Show me consumer groups handling regulatory reporting"

#### Risk Management
**Claude Prompts**:
- "List all risk calculation consumer groups"
- "What's the processing lag for market data streams?"
- "Are position update consumers running normally?"

### IoT and Manufacturing

#### Sensor Data Processing
```bash
# IoT sensor data configuration
export KAFKA_CLUSTER_NAME_1="factory-floor"
export KAFKA_BOOTSTRAP_SERVERS_1="factory-kafka:9092"

export KAFKA_CLUSTER_NAME_2="analytics"
export KAFKA_BOOTSTRAP_SERVERS_2="analytics-kafka:9092"
```

**Common Prompts**:
- "Show me all sensor data topics"
- "Which consumer groups are processing temperature data?"
- "What's the status of predictive maintenance consumers?"
- "Are there any alert processing delays?"

#### Quality Control
**Claude Prompts**:
- "Show me quality metrics streaming topics"
- "Which consumers are processing defect detection data?"
- "What's the current throughput for inspection results?"

## Advanced Scenarios

### Multi-Environment Management

#### Environment Comparison
**Scenario**: Comparing configurations across development, staging, and production.

**Setup**:
```bash
# Development
export KAFKA_CLUSTER_NAME_1="dev"
export KAFKA_BOOTSTRAP_SERVERS_1="dev-kafka:9092"
export READONLY_1="false"

# Staging
export KAFKA_CLUSTER_NAME_2="staging"
export KAFKA_BOOTSTRAP_SERVERS_2="staging-kafka:9092"
export READONLY_2="false"

# Production
export KAFKA_CLUSTER_NAME_3="prod"
export KAFKA_BOOTSTRAP_SERVERS_3="prod-kafka:9092"
export KAFKA_SECURITY_PROTOCOL_3="SASL_SSL"
export READONLY_3="true"
```

**Claude Prompts**:
- "Compare topic configurations between dev and prod"
- "Show me which consumer groups exist in production but not in staging"
- "What are the differences in partition counts across environments?"
- "Are all environments using the same replication factors?"

### Disaster Recovery Planning

#### Backup Cluster Monitoring
**Scenario**: Monitoring backup clusters and replication status.

**Claude Prompts**:
- "Show me the status of disaster recovery clusters"
- "Compare topic lists between primary and backup clusters"
- "Are all critical topics replicated to the backup cluster?"
- "What's the replication lag for disaster recovery?"

### Compliance and Auditing

#### Data Governance
**Scenario**: Ensuring compliance with data governance policies.

**Claude Prompts**:
- "Show me all topics containing personal data"
- "Which consumer groups have access to PII data?"
- "What's the retention policy for audit log topics?"
- "Are there any consumer groups with suspicious access patterns?"

## Integration Examples

### CI/CD Pipeline Integration

#### Automated Testing
**Scenario**: Integrating Kafka health checks into deployment pipelines.

```bash
# Health check script using MCP server
#!/bin/bash
# Check if deployment topics are ready
curl -X POST "http://kafka-brokers-mcp:8000" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call", 
    "params": {
      "name": "list_topics",
      "arguments": {"cluster": "staging"}
    },
    "id": 1
  }'
```

### Monitoring Integration

#### Alert Automation
**Scenario**: Integrating with monitoring systems for automated alerts.

**Claude Prompts for Alert Investigation**:
- "Show me the status of the alerting topic"
- "Which consumer groups are processing monitoring data?"
- "Are there any consumer lag alerts?"
- "What's the current health of metric collection topics?"

## Best Practices

### Security

1. **Readonly Mode for Production**:
   ```bash
   export READONLY="true"  # Prevent accidental modifications
   ```

2. **Secure Authentication**:
   ```bash
   export KAFKA_SECURITY_PROTOCOL="SASL_SSL"
   export KAFKA_SASL_MECHANISM="SCRAM-SHA-256"
   ```

3. **Minimal Permissions**:
   - Use dedicated service accounts with minimal required permissions
   - Separate credentials for different environments

### Operational

1. **Multi-Cluster Setup**:
   - Separate development, staging, and production clusters
   - Use descriptive cluster names
   - Apply appropriate readonly settings

2. **Monitoring Strategy**:
   - Regular health checks via Claude prompts
   - Automated alerting integration
   - Historical trend analysis

3. **Documentation**:
   - Document common Claude prompts for your use cases
   - Create team-specific prompt libraries
   - Share useful prompt patterns

## Troubleshooting Common Scenarios

### Consumer Lag Investigation

**Problem**: High consumer lag detected in monitoring.

**Investigation Prompts**:
- "Describe the consumer group with high lag"
- "Show me partition assignments for the slow consumer group"
- "What's the current offset vs high watermark for each partition?"
- "Are there any failed or stuck consumers in the group?"

### Topic Configuration Issues

**Problem**: Messages not being processed as expected.

**Investigation Prompts**:
- "Show me the configuration for the problematic topic"
- "What's the partition count and replication factor?"
- "Which consumer groups are subscribed to this topic?"
- "Are there any consumer groups in error state?"

### Broker Connectivity Issues

**Problem**: Applications can't connect to Kafka cluster.

**Investigation Prompts**:
- "Show me the status of all brokers"
- "Are all brokers healthy and accessible?"
- "What's the current cluster metadata?"
- "Which broker is the controller?"

## Getting Started Templates

### Development Team Setup
```bash
# Single cluster for development
export KAFKA_BOOTSTRAP_SERVERS="dev-kafka:9092"
export KAFKA_SECURITY_PROTOCOL="PLAINTEXT"
export READONLY="false"
```

### Operations Team Setup
```bash
# Multi-cluster production monitoring
export KAFKA_CLUSTER_NAME_1="production-us-east"
export KAFKA_BOOTSTRAP_SERVERS_1="prod-east-kafka:9092"
export KAFKA_SECURITY_PROTOCOL_1="SASL_SSL"
export READONLY_1="true"

export KAFKA_CLUSTER_NAME_2="production-us-west"
export KAFKA_BOOTSTRAP_SERVERS_2="prod-west-kafka:9092"
export KAFKA_SECURITY_PROTOCOL_2="SASL_SSL"
export READONLY_2="true"
```

### Analytics Team Setup
```bash
# Analytics cluster access
export KAFKA_BOOTSTRAP_SERVERS="analytics-kafka:9092"
export KAFKA_SECURITY_PROTOCOL="SASL_PLAINTEXT"
export KAFKA_SASL_MECHANISM="SCRAM-SHA-256"
export READONLY="true"  # Read-only access for analysts
```

This comprehensive use case guide demonstrates the versatility and power of the Kafka Brokers MCP Server across different roles, industries, and operational scenarios.
