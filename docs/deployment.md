# Deployment Guide

Comprehensive guide for deploying the Kafka Brokers MCP Server in various environments.

## Quick Start

### Docker (Recommended)

```bash
# Pull the latest stable image
docker pull aywengo/kafka-brokers-mcp:stable

# Run with basic configuration
docker run -d \
  -e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
  -e KAFKA_SECURITY_PROTOCOL=PLAINTEXT \
  -e READONLY=false \
  aywengo/kafka-brokers-mcp:stable
```

### Local Python

```bash
# Clone and install
git clone https://github.com/aywengo/kafka-brokers-mcp
cd kafka-brokers-mcp
pip install -r requirements.txt

# Configure environment
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export KAFKA_SECURITY_PROTOCOL="PLAINTEXT"
export READONLY="false"

# Run the server
python kafka_brokers_unified_mcp.py
```

## Production Deployment

### Docker Compose

Create a production-ready `docker-compose.yml`:

```yaml
version: '3.8'

services:
  kafka-brokers-mcp:
    image: aywengo/kafka-brokers-mcp:stable
    container_name: kafka-brokers-mcp-prod
    restart: unless-stopped
    environment:
      # Multi-cluster configuration
      - KAFKA_CLUSTER_NAME_1=development
      - KAFKA_BOOTSTRAP_SERVERS_1=dev-kafka:9092
      - KAFKA_SECURITY_PROTOCOL_1=PLAINTEXT
      - READONLY_1=false
      
      - KAFKA_CLUSTER_NAME_2=production
      - KAFKA_BOOTSTRAP_SERVERS_2=prod-kafka:9092
      - KAFKA_SECURITY_PROTOCOL_2=SASL_SSL
      - KAFKA_SASL_MECHANISM_2=SCRAM-SHA-256
      - KAFKA_SASL_USERNAME_2=prod-user
      - KAFKA_SASL_PASSWORD_2=${PROD_KAFKA_PASSWORD}
      - READONLY_2=true
    ports:
      - "38001:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - kafka-network
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

networks:
  kafka-network:
    driver: bridge
```

### Kubernetes

Deploy using Kubernetes manifests:

#### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka-brokers-mcp
  namespace: kafka-tools
  labels:
    app: kafka-brokers-mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kafka-brokers-mcp
  template:
    metadata:
      labels:
        app: kafka-brokers-mcp
    spec:
      containers:
      - name: kafka-brokers-mcp
        image: aywengo/kafka-brokers-mcp:stable
        ports:
        - containerPort: 8000
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka-service:9092"
        - name: KAFKA_SECURITY_PROTOCOL
          value: "SASL_SSL"
        - name: KAFKA_SASL_MECHANISM
          value: "SCRAM-SHA-256"
        - name: KAFKA_SASL_USERNAME
          valueFrom:
            secretKeyRef:
              name: kafka-credentials
              key: username
        - name: KAFKA_SASL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: kafka-credentials
              key: password
        - name: READONLY
          value: "true"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 10
      imagePullPolicy: IfNotPresent
```

#### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: kafka-brokers-mcp-service
  namespace: kafka-tools
spec:
  selector:
    app: kafka-brokers-mcp
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### Secret for Credentials
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kafka-credentials
  namespace: kafka-tools
type: Opaque
data:
  username: <base64-encoded-username>
  password: <base64-encoded-password>
```

### Helm Chart

Create a Helm chart for easier deployment:

#### values.yaml
```yaml
replicaCount: 2

image:
  repository: aywengo/kafka-brokers-mcp
  tag: stable
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8000

kafka:
  clusters:
    - name: production
      bootstrapServers: prod-kafka:9092
      securityProtocol: SASL_SSL
      saslMechanism: SCRAM-SHA-256
      readonly: true
      credentials:
        existingSecret: kafka-prod-credentials
        usernameKey: username
        passwordKey: password

resources:
  requests:
    memory: 256Mi
    cpu: 250m
  limits:
    memory: 512Mi
    cpu: 500m

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 80

healthCheck:
  enabled: true
  path: /health
```

## Cloud Platform Deployment

### AWS ECS

#### Task Definition
```json
{
  "family": "kafka-brokers-mcp",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "kafka-brokers-mcp",
      "image": "aywengo/kafka-brokers-mcp:stable",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "KAFKA_BOOTSTRAP_SERVERS",
          "value": "kafka-cluster.amazonaws.com:9092"
        },
        {
          "name": "KAFKA_SECURITY_PROTOCOL",
          "value": "SASL_SSL"
        },
        {
          "name": "READONLY",
          "value": "true"
        }
      ],
      "secrets": [
        {
          "name": "KAFKA_SASL_USERNAME",
          "valueFrom": "arn:aws:ssm:region:account:parameter/kafka/username"
        },
        {
          "name": "KAFKA_SASL_PASSWORD",
          "valueFrom": "arn:aws:ssm:region:account:parameter/kafka/password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/kafka-brokers-mcp",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy kafka-brokers-mcp \
  --image=aywengo/kafka-brokers-mcp:stable \
  --platform=managed \
  --region=us-central1 \
  --set-env-vars="KAFKA_BOOTSTRAP_SERVERS=kafka-cluster:9092,KAFKA_SECURITY_PROTOCOL=SASL_SSL,READONLY=true" \
  --set-secrets="KAFKA_SASL_USERNAME=kafka-username:latest,KAFKA_SASL_PASSWORD=kafka-password:latest" \
  --port=8000 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=10
```

### Azure Container Instances

```yaml
apiVersion: 2021-09-01
location: eastus
name: kafka-brokers-mcp
properties:
  containers:
  - name: kafka-brokers-mcp
    properties:
      image: aywengo/kafka-brokers-mcp:stable
      ports:
      - port: 8000
        protocol: TCP
      environmentVariables:
      - name: KAFKA_BOOTSTRAP_SERVERS
        value: kafka-cluster.eastus.cloudapp.azure.com:9092
      - name: KAFKA_SECURITY_PROTOCOL
        value: SASL_SSL
      - name: READONLY
        value: "true"
      - name: KAFKA_SASL_USERNAME
        secureValue: "{{kafka-username}}"
      - name: KAFKA_SASL_PASSWORD
        secureValue: "{{kafka-password}}"
      resources:
        requests:
          cpu: 0.5
          memoryInGB: 1
        limits:
          cpu: 1
          memoryInGB: 2
  osType: Linux
  restartPolicy: Always
type: Microsoft.ContainerInstance/containerGroups
```

## Security Configuration

### SSL/TLS Setup

```bash
# For SSL-enabled Kafka clusters
export KAFKA_SECURITY_PROTOCOL="SSL"
export KAFKA_SSL_CA_LOCATION="/certs/ca-cert.pem"
export KAFKA_SSL_CERTIFICATE_LOCATION="/certs/client-cert.pem"
export KAFKA_SSL_KEY_LOCATION="/certs/client-key.pem"
```

### SASL Authentication

```bash
# SCRAM-SHA-256 (recommended)
export KAFKA_SECURITY_PROTOCOL="SASL_SSL"
export KAFKA_SASL_MECHANISM="SCRAM-SHA-256"
export KAFKA_SASL_USERNAME="kafka-user"
export KAFKA_SASL_PASSWORD="secure-password"

# SCRAM-SHA-512
export KAFKA_SASL_MECHANISM="SCRAM-SHA-512"

# PLAIN (not recommended for production)
export KAFKA_SASL_MECHANISM="PLAIN"
```

### Network Security

1. **Firewall Rules**: Restrict access to Kafka ports (9092, 9093, etc.)
2. **VPC/Network Isolation**: Deploy in private networks
3. **Load Balancer**: Use SSL termination at load balancer level
4. **Service Mesh**: Integrate with Istio or similar for mTLS

## Monitoring and Observability

### Health Checks

The server provides health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed status via MCP resources
# Access via Claude Desktop or MCP client
```

### Logging

Structured logging configuration:

```python
# Environment variables for logging
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
export LOG_FORMAT="json"  # json, text
```

### Metrics

Integrate with monitoring systems:

#### Prometheus
```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

#### Grafana
```yaml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Performance Tuning

### Resource Allocation

```yaml
# Kubernetes resource recommendations
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### JVM Tuning (if using Java-based deployment)

```bash
export JAVA_OPTS="-Xms256m -Xmx512m -XX:+UseG1GC"
```

### Connection Pooling

```python
# Adjust in configuration
max_workers = 20  # ThreadPoolExecutor workers
connection_timeout = 30  # Kafka connection timeout
request_timeout = 10  # Kafka request timeout
```

## Backup and Recovery

### Configuration Backup

```bash
# Backup configuration
kubectl get configmap kafka-brokers-mcp-config -o yaml > backup-config.yaml
kubectl get secret kafka-credentials -o yaml > backup-secrets.yaml
```

### Disaster Recovery

1. **Multi-Region Deployment**: Deploy in multiple regions
2. **Configuration Replication**: Sync configurations across environments
3. **Monitoring**: Set up alerts for service health

## Troubleshooting

### Common Issues

#### Connection Problems
```bash
# Test Kafka connectivity
kafka-console-consumer --bootstrap-server localhost:9092 --topic __consumer_offsets --from-beginning --max-messages 1

# Check DNS resolution
nslookup kafka-cluster.example.com

# Verify network connectivity
telnet kafka-cluster.example.com 9092
```

#### Authentication Failures
```bash
# Verify credentials
echo $KAFKA_SASL_USERNAME
echo $KAFKA_SASL_PASSWORD

# Test SASL authentication
kafka-console-consumer --bootstrap-server localhost:9092 \
  --consumer-property security.protocol=SASL_SSL \
  --consumer-property sasl.mechanism=SCRAM-SHA-256 \
  --consumer-property sasl.jaas.config='org.apache.kafka.common.security.scram.ScramLoginModule required username="user" password="pass";' \
  --topic test-topic
```

#### Memory Issues
```bash
# Monitor memory usage
docker stats kafka-brokers-mcp

# Check logs for OOM errors
docker logs kafka-brokers-mcp | grep -i memory
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL="DEBUG"

# Verbose MCP tool output
# Available in integration with Claude Desktop
```

## Maintenance

### Updates

```bash
# Pull latest image
docker pull aywengo/kafka-brokers-mcp:stable

# Rolling update in Kubernetes
kubectl rollout restart deployment/kafka-brokers-mcp

# Zero-downtime update with multiple replicas
kubectl set image deployment/kafka-brokers-mcp kafka-brokers-mcp=aywengo/kafka-brokers-mcp:v1.1.0
```

### Scaling

```bash
# Scale horizontally
kubectl scale deployment kafka-brokers-mcp --replicas=5

# Auto-scaling based on CPU
kubectl autoscale deployment kafka-brokers-mcp --cpu-percent=80 --min=2 --max=10
```

## Support

For additional support:

- **Documentation**: [GitHub Repository](https://github.com/aywengo/kafka-brokers-mcp)
- **Issues**: [GitHub Issues](https://github.com/aywengo/kafka-brokers-mcp/issues)
- **Community**: [Discussions](https://github.com/aywengo/kafka-brokers-mcp/discussions)
- **Docker Hub**: [aywengo/kafka-brokers-mcp](https://hub.docker.com/r/aywengo/kafka-brokers-mcp)
