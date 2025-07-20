#!/bin/bash

# Fix Python code formatting with Black

set -e

echo "🎨 Running Black code formatter..."

# Check if black is installed
if ! command -v black &> /dev/null; then
    echo "Installing Black..."
    pip install black
fi

# Run black on all Python files
echo "Formatting Python files..."
black --line-length 127 --target-version py311 --target-version py312 .

echo "✅ Code formatting complete!"

# Show which files were reformatted
if [ -n "$(git status --porcelain)" ]; then
    echo ""
    echo "Files that were reformatted:"
    git status --short | grep '.py$' || true
else
    echo "All files were already properly formatted."
fi