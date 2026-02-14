"""
Application Configuration
Central configuration for FastAPI application
"""

import os
from pathlib import Path

# TensorFlow/Keras optimization for deployment
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF warnings
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'  # Don't allocate all GPU memory
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN optimizations (reduce memory)
os.environ['KMP_AFFINITY'] = 'disabled'  # Disable thread affinity
os.environ['OMP_NUM_THREADS'] = '2'  # Limit OpenMP threads
os.environ['TF_NUM_INTRAOP_THREADS'] = '2'  # Limit TensorFlow parallelism
os.environ['TF_NUM_INTEROP_THREADS'] = '2'  # Limit TensorFlow inter-op parallelism

# App metadata
APP_TITLE = "AI Crypto Trading API"
APP_DESCRIPTION = "Real money AI-powered cryptocurrency auto trading platform"
APP_VERSION = "1.0.0"

# CORS settings
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

# Cookie security — auto-detect HTTPS from known origins
_any_origin = os.environ.get('CORS_ORIGINS', '') + os.environ.get('REACT_APP_BACKEND_URL', '')
IS_HTTPS = _any_origin.startswith('https://') or 'https://' in _any_origin
COOKIE_SECURE = IS_HTTPS
COOKIE_SAMESITE = "lax"

# Logging configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
