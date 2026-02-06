#!/bin/bash
# Build script with increased Node memory to prevent heap allocation failures
# This fixes the recurring "Ineffective mark-compacts near heap limit" error

set -e

echo "🔧 Starting optimized frontend build..."

# Clean previous build artifacts to reduce memory pressure
rm -rf build 2>/dev/null || true

# Set Node.js memory options
export NODE_OPTIONS="--max-old-space-size=4096"

# Disable source maps in production to reduce memory usage (optional flag)
# Uncomment the line below if builds still fail:
# export GENERATE_SOURCEMAP=false

# Run garbage collection more aggressively
export NODE_OPTIONS="$NODE_OPTIONS --expose-gc"

echo "📦 Building with NODE_OPTIONS: $NODE_OPTIONS"

# Run the build
yarn craco build

echo "✅ Frontend build completed successfully!"
