#!/bin/bash

# Script to fix executable permissions for all shell scripts in the repository
# This should be run locally before committing to ensure scripts have proper permissions

echo "🔧 Setting executable permissions for shell scripts..."

# Find all .sh files and make them executable
find . -name "*.sh" -type f | while read -r script; do
    echo "Setting +x on: $script"
    chmod +x "$script"
done

echo "✅ Done! All shell scripts now have executable permissions."
echo ""
echo "💡 To verify in Git, run:"
echo "   git ls-files --stage | grep '\.sh$'"
echo ""
echo "   Files with mode 100755 are executable"
echo "   Files with mode 100644 are not executable"
