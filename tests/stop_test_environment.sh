#!/bin/bash

MODE=${1:-"normal"}  # normal, clean, silent

# Colors (only if not silent)
if [ "$MODE" != "silent" ]; then
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    RED='\033[0;31m'
    NC='\033[0m'
else
    GREEN=''
    YELLOW=''
    BLUE=''
    RED=''
    NC=''
fi

# Function to determine which docker compose command to use
docker_compose_cmd() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
    else
        if [ "$MODE" != "silent" ]; then
            echo -e "${RED}❌ Neither 'docker compose' nor 'docker-compose' is available${NC}" >&2
        fi
        exit 1
    fi
}

DOCKER_COMPOSE=$(docker_compose_cmd)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$MODE" != "silent" ]; then
    echo -e "${BLUE}🛑 Stopping Kafka Brokers Test Environment${NC}"
fi

# Stop services
if [ "$MODE" != "silent" ]; then
    echo -e "${YELLOW}⏳ Stopping Docker services...${NC}"
fi

$DOCKER_COMPOSE -f docker-compose.test.yml down 2>/dev/null || true

if [ "$MODE" == "clean" ]; then
    if [ "$MODE" != "silent" ]; then
        echo -e "${YELLOW}🧹 Cleaning up volumes and networks...${NC}"
    fi
    $DOCKER_COMPOSE -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
    
    # Remove any dangling volumes
    docker volume prune -f 2>/dev/null || true
fi

if [ "$MODE" != "silent" ]; then
    echo -e "${GREEN}✅ Test environment stopped${NC}"
fi