#!/bin/bash
# Build script with increased Node memory to prevent heap allocation failures
# This fixes the recurring "Ineffective mark-compacts near heap limit" error

export NODE_OPTIONS="--max-old-space-size=4096"
yarn craco build
