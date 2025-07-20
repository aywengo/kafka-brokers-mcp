#!/bin/bash

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

MODE=${1:-"multi"}  # dev, multi, ui

# Function to determine which docker compose command to use
docker_compose_cmd() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
    else
        echo -e "${RED}❌ Neither 'docker compose' nor 'docker-compose' is available${NC}" >&2
        exit 1
    fi
}

DOCKER_COMPOSE=$(docker_compose_cmd)

print_usage() {
    echo "Usage: $0 [MODE]"
    echo "Modes:"
    echo "  dev   - Single Kafka broker (for single-cluster tests)"
    echo "  multi - Multiple Kafka clusters (for multi-cluster tests)"
    echo "  ui    - Multi + Kafka UI for monitoring"
    echo ""
    echo "Default: multi"
}

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    print_usage
    exit 0
fi

echo -e "${BLUE}🚀 Starting Kafka Brokers Test Environment${NC}"
echo -e "${YELLOW}Mode: $MODE${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Stop any existing environment
./stop_test_environment.sh silent 2>/dev/null || true

case $MODE in
    "dev")
        echo -e "${BLUE}🔧 Starting single Kafka cluster...${NC}"
        COMPOSE_FILE="docker-compose.test.yml"
        SERVICES="zookeeper kafka"
        ;;
    "multi")
        echo -e "${BLUE}🔧 Starting multiple Kafka clusters...${NC}"
        COMPOSE_FILE="docker-compose.test.yml"
        SERVICES="zookeeper kafka kafka-cluster-2"
        ;;
    "ui")
        echo -e "${BLUE}🔧 Starting multiple clusters with UI...${NC}"
        COMPOSE_FILE="docker-compose.test.yml"
        SERVICES="zookeeper kafka kafka-cluster-2 kafka-ui"
        ;;
    *)
        echo -e "${RED}❌ Invalid mode: $MODE${NC}"
        print_usage
        exit 1
        ;;
esac

# Start services
echo -e "${YELLOW}⏳ Starting services: $SERVICES${NC}"
$DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d $SERVICES

# Wait for services
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"

# Wait for Kafka to be ready
echo -e "${BLUE}🔍 Waiting for Kafka cluster 1...${NC}"
timeout=60
count=0
while ! $DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list >/dev/null 2>&1; do
    sleep 2
    count=$((count + 1))
    if [ $count -gt $((timeout / 2)) ]; then
        echo -e "${RED}❌ Kafka cluster 1 failed to start within ${timeout}s${NC}"
        exit 1
    fi
done

if [[ "$MODE" == "multi" || "$MODE" == "ui" ]]; then
    echo -e "${BLUE}🔍 Waiting for Kafka cluster 2...${NC}"
    count=0
    while ! $DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T kafka-cluster-2 kafka-topics --bootstrap-server localhost:9093 --list >/dev/null 2>&1; do
        sleep 2
        count=$((count + 1))
        if [ $count -gt $((timeout / 2)) ]; then
            echo -e "${RED}❌ Kafka cluster 2 failed to start within ${timeout}s${NC}"
            exit 1
        fi
    done
fi

# Create test topics
echo -e "${BLUE}📝 Creating test topics...${NC}"

# Topics for cluster 1
$DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T kafka kafka-topics \
    --bootstrap-server localhost:9092 \
    --create \
    --topic test-topic-1 \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists

$DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T kafka kafka-topics \
    --bootstrap-server localhost:9092 \
    --create \
    --topic test-topic-2 \
    --partitions 2 \
    --replication-factor 1 \
    --if-not-exists

if [[ "$MODE" == "multi" || "$MODE" == "ui" ]]; then
    # Topics for cluster 2
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T kafka-cluster-2 kafka-topics \
        --bootstrap-server localhost:9093 \
        --create \
        --topic prod-topic-1 \
        --partitions 5 \
        --replication-factor 1 \
        --if-not-exists
fi

echo -e "${GREEN}✅ Test environment ready!${NC}"
echo ""
echo -e "${BLUE}📋 Environment Details:${NC}"
echo "  Kafka Cluster 1: localhost:9092"
if [[ "$MODE" == "multi" || "$MODE" == "ui" ]]; then
    echo "  Kafka Cluster 2: localhost:9093"
fi
if [[ "$MODE" == "ui" ]]; then
    echo "  Kafka UI: http://localhost:8080"
fi
echo ""
echo -e "${YELLOW}💡 Useful commands:${NC}"
echo "  Check logs: $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f [service]"
echo "  List topics: $DOCKER_COMPOSE -f $COMPOSE_FILE exec kafka kafka-topics --bootstrap-server localhost:9092 --list"
echo "  Stop environment: ./stop_test_environment.sh"