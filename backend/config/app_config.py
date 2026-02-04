"""
Application Configuration
Central configuration for FastAPI application
"""

import os
from pathlib import Path

# App metadata
APP_TITLE = "AI Crypto Trading API"
APP_DESCRIPTION = "Real money AI-powered cryptocurrency auto trading platform"
APP_VERSION = "1.0.0"

# CORS settings
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

# Logging configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
