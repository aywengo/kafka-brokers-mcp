#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

MCP_SERVER_URL="http://localhost:8000"

echo -e "${BLUE}🔍 Opening MCP Inspector...${NC}"
echo -e "${YELLOW}Connecting to: $MCP_SERVER_URL${NC}"

# Check if the MCP server is running
if ! curl -s "$MCP_SERVER_URL" > /dev/null; then
    echo -e "${RED}❌ MCP server is not running at $MCP_SERVER_URL${NC}"
    echo -e "${YELLOW}💡 Start the test environment first:${NC}"
    echo "   ./start_test_environment.sh dev|multi|ui"
    exit 1
fi

echo -e "${GREEN}✅ MCP server is running${NC}"
echo -e "${BLUE}🚀 Launching MCP Inspector...${NC}"

# Launch the MCP inspector
npx @modelcontextprotocol/inspector "$MCP_SERVER_URL" 