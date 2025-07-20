#!/bin/bash

# Format all Python code in the project (including scripts and tests)

set -e

echo "🎨 Formatting all Python code..."

# Check if black is installed
if ! command -v black &> /dev/null; then
    echo "Installing Black..."
    pip install black
fi

# Format all Python files
echo "Formatting Python files..."
black --line-length 127 --target-version py311 --target-version py312 .

echo "✅ All code formatting complete!"

# Show which files were reformatted
if [ -n "$(git status --porcelain)" ]; then
    echo ""
    echo "Files that were reformatted:"
    git status --short | grep '.py$' || true
else
    echo "All files were already properly formatted."
fi