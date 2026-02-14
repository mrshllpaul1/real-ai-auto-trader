"""
Input Sanitization Utility
Prevents NoSQL injection and other malicious input attacks.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# MongoDB operators that should NEVER appear in user input
DANGEROUS_MONGO_OPERATORS = [
    '$gt', '$gte', '$lt', '$lte', '$ne', '$nin', '$in',
    '$or', '$and', '$not', '$nor', '$exists', '$type',
    '$mod', '$regex', '$text', '$where', '$all', '$elemMatch',
    '$size', '$slice', '$meta', '$push', '$pull', '$addToSet',
    '$pop', '$rename', '$set', '$unset', '$inc', '$mul',
    '$min', '$max', '$currentDate', '$bit',
    '$expr', '$jsonSchema', '$comment',
    '$lookup', '$project', '$match', '$group', '$sort',
    '$limit', '$skip', '$unwind', '$replaceRoot',
]

# Patterns that indicate potential injection
DANGEROUS_PATTERNS = [
    re.compile(r'\$[a-zA-Z]+'),      # MongoDB operators
    re.compile(r'\{\s*\$'),           # Object starting with $
    re.compile(r'javascript:', re.I),  # JavaScript protocol
    re.compile(r'<script', re.I),      # XSS attempt
]


def sanitize_string(value: str, max_length: int = 10000) -> str:
    """
    Sanitize a string input.
    
    - Strips leading/trailing whitespace
    - Truncates to max_length
    - Removes null bytes
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Strip whitespace
    value = value.strip()
    
    # Truncate
    if len(value) > max_length:
        value = value[:max_length]
    
    return value


def check_nosql_injection(value: Any) -> bool:
    """
    Check if a value contains potential NoSQL injection patterns.
    Returns True if the value is SAFE, False if suspicious.
    """
    if isinstance(value, str):
        # Check for MongoDB operators in string
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(value):
                logger.warning(f"Potential NoSQL injection detected in string: {value[:100]}")
                return False
        return True
    
    elif isinstance(value, dict):
        for key, val in value.items():
            # Check if key is a MongoDB operator
            if isinstance(key, str) and key.startswith('$'):
                logger.warning(f"Potential NoSQL injection: MongoDB operator '{key}' in input")
                return False
            # Recursively check values
            if not check_nosql_injection(val):
                return False
        return True
    
    elif isinstance(value, list):
        return all(check_nosql_injection(item) for item in value)
    
    # Primitive types (int, float, bool, None) are safe
    return True


def sanitize_mongo_query_param(value: str) -> str:
    """
    Sanitize a value that will be used in a MongoDB query.
    Strips any MongoDB operator prefixes.
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove any $ prefix which could be an operator
    while value.startswith('$'):
        value = value[1:]
    
    return sanitize_string(value)


def sanitize_coin_id(coin_id: str) -> str:
    """
    Sanitize a cryptocurrency identifier.
    Only allows alphanumeric, hyphens, underscores.
    """
    if not isinstance(coin_id, str):
        return ""
    
    # Only allow safe characters for coin IDs
    sanitized = re.sub(r'[^a-zA-Z0-9\-_.]', '', coin_id)
    return sanitized[:50]  # Max 50 chars for coin ID


def sanitize_symbol(symbol: str) -> str:
    """
    Sanitize a trading symbol (e.g., BTC, XBTUSD).
    Only allows uppercase alphanumeric and common separators.
    """
    if not isinstance(symbol, str):
        return ""
    
    sanitized = re.sub(r'[^a-zA-Z0-9/\-_]', '', symbol)
    return sanitized.upper()[:20]


def sanitize_user_id(user_id: str) -> str:
    """
    Sanitize a user identifier.
    Only allows alphanumeric, hyphens, underscores.
    """
    if not isinstance(user_id, str):
        return "unknown"
    
    sanitized = re.sub(r'[^a-zA-Z0-9\-_@.]', '', user_id)
    return sanitized[:100] if sanitized else "unknown"


def sanitize_dict(data: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary, removing MongoDB operators.
    """
    if max_depth <= 0:
        return {}
    
    sanitized = {}
    for key, value in data.items():
        # Skip keys that look like MongoDB operators
        if isinstance(key, str) and key.startswith('$'):
            logger.warning(f"Removed potential injection key: {key}")
            continue
        
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_dict(v, max_depth - 1) if isinstance(v, dict) else v for v in value]
        else:
            sanitized[key] = value
    
    return sanitized
