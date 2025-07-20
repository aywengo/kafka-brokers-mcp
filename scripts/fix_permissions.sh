#!/bin/bash

# Fix permissions for all shell scripts in the repository

set -e

echo "Fixing permissions for shell scripts..."

# Find all .sh files and make them executable
find . -name "*.sh" -type f | while read -r file; do
    echo "Making $file executable"
    chmod +x "$file"
done

echo "✅ All shell scripts are now executable"

# Specifically ensure test scripts are executable
if [ -d "tests" ]; then
    echo "Ensuring test scripts have proper permissions..."
    chmod +x tests/*.sh 2>/dev/null || true
fi

echo "✅ Permission fixes complete"