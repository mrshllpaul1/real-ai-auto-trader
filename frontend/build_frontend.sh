#!/bin/bash
# Robust frontend build script

set -e
cd /app/frontend

echo "=== Starting Frontend Build ===" 
echo "Time: $(date)"

# Clean old build
rm -rf build 2>/dev/null || true

# Set memory and disable source maps
export NODE_OPTIONS="--max-old-space-size=4096"
export GENERATE_SOURCEMAP=false
export CI=true

# Run build
echo "Running yarn craco build..."
yarn craco build

echo "=== Build Complete ===" 
echo "Time: $(date)"
ls -la build/
