FROM python:3.11-slim

LABEL maintainer="aywengo"
LABEL description="Kafka Brokers MCP Server - A comprehensive MCP server for Kafka broker operations"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY kafka_brokers_unified_mcp.py .
COPY kafka_cluster_manager.py .
COPY kafka_mcp_resources.py .
COPY kafka_mcp_tools.py .
    
# Create non-root user
RUN groupadd -r kafkamcp && useradd -r -g kafkamcp kafkamcp
RUN chown -R kafkamcp:kafkamcp /app
USER kafkamcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f kafka_brokers_unified_mcp.py || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default command
CMD ["python", "kafka_brokers_unified_mcp.py"]