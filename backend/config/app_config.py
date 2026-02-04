"""
Application Configuration Module
Handles FastAPI app creation, middleware, and logging setup
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="AI Crypto Trading API",
        description="Real money AI-powered cryptocurrency auto trading platform",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


def setup_logging() -> logging.Logger:
    """Configure and return the application logger"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)
