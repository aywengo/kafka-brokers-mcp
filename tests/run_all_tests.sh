#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Default values
QUICK_MODE=false
NO_CLEANUP=false
VERBOSE=false
TEST_PATTERN=""

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --quick, -q          Run essential tests only (faster)"
    echo "  --no-cleanup, -n     Keep test environment running after tests"
    echo "  --verbose, -v        Verbose output"
    echo "  --pattern PATTERN    Run tests matching pattern"
    echo "  --help, -h           Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                   # Run all tests"
    echo "  $0 --quick          # Run essential tests only"
    echo "  $0 --pattern topic   # Run tests with 'topic' in name"
    echo "  $0 --no-cleanup     # Keep environment running for debugging"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick|-q)
            QUICK_MODE=true
            shift
            ;;
        --no-cleanup|-n)
            NO_CLEANUP=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --pattern)
            TEST_PATTERN="$2"
            shift 2
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🚀 Kafka Brokers MCP Server - Test Suite${NC}"
echo "========================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Discover available test files (exclude utility modules)
AVAILABLE_TEST_FILES=()
for file in test_*.py; do
    if [ -f "$file" ] && [ "$file" != "test_utils.py" ]; then
        AVAILABLE_TEST_FILES+=("$file")
    fi
done

if [ ${#AVAILABLE_TEST_FILES[@]} -eq 0 ]; then
    echo -e "${RED}❌ No test files found in $(pwd)${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Found ${#AVAILABLE_TEST_FILES[@]} test files: ${AVAILABLE_TEST_FILES[*]}${NC}"

# Test files based on mode
if [ "$QUICK_MODE" = true ]; then
    echo -e "${YELLOW}⚡ Running in QUICK mode (essential tests only)${NC}"
    TEST_FILES=()
    # Only include essential tests that exist
    for test in "test_basic_server.py" "test_topic_operations.py" "test_consumer_group_operations.py"; do
        if [[ " ${AVAILABLE_TEST_FILES[@]} " =~ " ${test} " ]]; then
            TEST_FILES+=("$test")
        fi
    done
else
    echo -e "${BLUE}🔍 Running FULL test suite${NC}"
    TEST_FILES=("${AVAILABLE_TEST_FILES[@]}")
fi

# Filter tests by pattern if provided
if [ -n "$TEST_PATTERN" ]; then
    echo -e "${YELLOW}🔍 Filtering tests by pattern: $TEST_PATTERN${NC}"
    FILTERED_FILES=()
    for file in "${TEST_FILES[@]}"; do
        if [[ "$file" == *"$TEST_PATTERN"* ]]; then
            FILTERED_FILES+=("$file")
        fi
    done
    TEST_FILES=("${FILTERED_FILES[@]}")
    
    if [ ${#TEST_FILES[@]} -eq 0 ]; then
        echo -e "${RED}❌ No tests match pattern: $TEST_PATTERN${NC}"
        exit 1
    fi
fi

echo "Tests to run: ${TEST_FILES[*]}"
echo ""

# Function to cleanup
cleanup() {
    if [ "$NO_CLEANUP" = false ]; then
        echo -e "${YELLOW}🧹 Cleaning up test environment...${NC}"
        ./stop_test_environment.sh clean 2>/dev/null || true
    else
        echo -e "${YELLOW}⚠️  Keeping test environment running (--no-cleanup flag)${NC}"
        echo "To stop manually: ./stop_test_environment.sh clean"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Check if test environment scripts exist
if [ ! -f "start_test_environment.sh" ]; then
    echo -e "${RED}❌ start_test_environment.sh not found${NC}"
    exit 1
fi

if [ ! -f "stop_test_environment.sh" ]; then
    echo -e "${RED}❌ stop_test_environment.sh not found${NC}"
    exit 1
fi

# Start test environment
echo -e "${BLUE}🔧 Starting test environment...${NC}"
if ! ./start_test_environment.sh multi; then
    echo -e "${RED}❌ Failed to start test environment${NC}"
    exit 1
fi

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check if Kafka is accessible
echo -e "${BLUE}🔍 Verifying Kafka connectivity...${NC}"
if ! $DOCKER_COMPOSE -f docker-compose.yml exec -T kafka-dev kafka-topics --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Warning: Kafka connectivity check failed, but continuing...${NC}"
else
    echo -e "${GREEN}✅ Kafka is accessible${NC}"
fi

echo -e "${GREEN}✅ Test environment ready${NC}"
echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null && ! python3 -m pytest --version &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio
fi

# Run tests
FAILED_TESTS=()
PASSED_TESTS=()
TOTAL_TESTS=${#TEST_FILES[@]}
CURRENT_TEST=0

for test_file in "${TEST_FILES[@]}"; do
    CURRENT_TEST=$((CURRENT_TEST + 1))
    echo -e "${BLUE}📋 Running test [$CURRENT_TEST/$TOTAL_TESTS]: $test_file${NC}"
    
    if [ "$VERBOSE" = true ]; then
        PYTEST_ARGS="-v -s"
    else
        PYTEST_ARGS="-v"
    fi
    
    if python3 run_single_test.py "$test_file" 2>&1; then
        echo -e "${GREEN}✅ PASSED: $test_file${NC}"
        PASSED_TESTS+=("$test_file")
    else
        echo -e "${RED}❌ FAILED: $test_file${NC}"
        FAILED_TESTS+=("$test_file")
    fi
    echo ""
done

# Summary
echo "========================================"
echo -e "${BLUE}📊 Test Results Summary${NC}"
echo "========================================"
echo "Total tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}${#PASSED_TESTS[@]}${NC}"
echo -e "Failed: ${RED}${#FAILED_TESTS[@]}${NC}"

if [ ${#PASSED_TESTS[@]} -gt 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Passed tests:${NC}"
    for test in "${PASSED_TESTS[@]}"; do
        echo "  - $test"
    done
fi

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Failed tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
    echo -e "${RED}💡 To debug failed tests:${NC}"
    echo "  1. Run: ./run_all_tests.sh --no-cleanup --verbose"
    echo "  2. Access logs: $DOCKER_COMPOSE -f docker-compose.yml logs"
    echo "  3. Run single test: python3 -m pytest -v -s <test_file>"
    
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
exit 0