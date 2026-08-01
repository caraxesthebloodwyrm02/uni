#!/usr/bin/env bash
# check-large-files.sh - Check for files that exceed size limits
# Prevents accidental commits of large files

set -euo pipefail

MAX_SIZE_KB=500  # 500KB limit for code files
MAX_SIZE_MB=5    # 5MB limit for any file

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Checking for large files..."

# Check staged files
large_files=$(git diff --cached --name-only --diff-filter=ACM | while read file; do
    if [ -f "$file" ]; then
        size=$(du -k "$file" | cut -f1)
        if [ "$size" -gt "$MAX_SIZE_KB" ]; then
            echo "$file ($size KB)"
        fi
    fi
done)

if [ -n "$large_files" ]; then
    echo -e "${RED}✗ Large files detected:${NC}"
    echo "$large_files"
    echo -e "${YELLOW}Maximum size: ${MAX_SIZE_KB}KB for code files${NC}"
    exit 1
fi

echo -e "${GREEN}✓ No large files found${NC}"
exit 0