"""
Response Compression Middleware
Enables gzip compression for API responses to reduce bandwidth usage
"""

import gzip
import logging
from io import BytesIO
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to compress HTTP responses using gzip
    Reduces response sizes by 60-80% for JSON/text data
    """
    
    def __init__(
        self,
        app,
        minimum_size: int = 500,  # Only compress responses > 500 bytes
        compression_level: int = 6,  # Balance between speed and compression (1-9)
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
    
    def _should_compress(self, request: Request, content_type: str, content_length: int) -> bool:
        """Determine if response should be compressed"""
        
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return False
        
        # Check content size
        if content_length < self.minimum_size:
            return False
        
        # Check content type (compress text-based formats)
        compressible_types = [
            "application/json",
            "application/javascript",
            "text/html",
            "text/css",
            "text/plain",
            "text/xml",
            "application/xml",
        ]
        
        return any(ct in content_type for ct in compressible_types)
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Get content type and length
        content_type = response.headers.get("content-type", "")
        content_length = int(response.headers.get("content-length", 0))
        
        # Check if we should compress
        if not self._should_compress(request, content_type, content_length):
            return response
        
        try:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Check actual body size
            if len(body) < self.minimum_size:
                # Return uncompressed for small responses
                return StreamingResponse(
                    iter([body]),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=content_type
                )
            
            # Compress the body
            compressed_body = gzip.compress(body, compresslevel=self.compression_level)
            
            # Calculate compression ratio
            compression_ratio = (1 - len(compressed_body) / len(body)) * 100 if len(body) > 0 else 0
            
            # Log compression stats for monitoring
            logger.debug(
                f"Compressed {request.url.path}: "
                f"{len(body)} -> {len(compressed_body)} bytes "
                f"({compression_ratio:.1f}% reduction)"
            )
            
            # Update headers
            headers = dict(response.headers)
            headers["content-encoding"] = "gzip"
            headers["content-length"] = str(len(compressed_body))
            headers["vary"] = "Accept-Encoding"
            
            # Return compressed response
            return StreamingResponse(
                iter([compressed_body]),
                status_code=response.status_code,
                headers=headers,
                media_type=content_type
            )
            
        except Exception as e:
            logger.error(f"Compression error: {str(e)}")
            # Return original response on error
            return response
