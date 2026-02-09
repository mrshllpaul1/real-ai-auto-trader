"""
Environment Variable Validation
Validates that critical environment variables are properly configured at startup.
"""

import os
import sys
from typing import List, Tuple
from cryptography.fernet import Fernet


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def validate_env_var(var_name: str, required: bool = True, min_length: int = 10) -> Tuple[bool, str]:
    """
    Validate a single environment variable.
    
    Args:
        var_name: Name of the environment variable
        required: Whether the variable is required
        min_length: Minimum length for the value
    
    Returns:
        Tuple of (is_valid, message)
    """
    value = os.getenv(var_name)
    
    if not value:
        if required:
            return False, f"❌ {var_name} is REQUIRED but not set"
        else:
            return True, f"⚠️  {var_name} is optional and not set"
    
    if len(value) < min_length:
        return False, f"❌ {var_name} is too short (minimum {min_length} characters)"
    
    # Check for placeholder values
    placeholder_indicators = [
        'your_', 'your-', '<your', 'example', 'placeholder', 
        'test_key', 'fake_', 'mock_', '_here'
    ]
    if any(indicator in value.lower() for indicator in placeholder_indicators):
        if required:
            return False, f"❌ {var_name} contains placeholder value - set real credential"
        else:
            return True, f"⚠️  {var_name} contains placeholder value"
    
    return True, f"✅ {var_name} is properly set"


def validate_encryption_key() -> Tuple[bool, str]:
    """Validate the ENCRYPTION_KEY for Fernet encryption."""
    key = os.getenv("ENCRYPTION_KEY")
    
    if not key:
        return False, "❌ ENCRYPTION_KEY is CRITICAL but not set - credentials will be lost on restart!"
    
    try:
        # Try to create a Fernet cipher with the key
        if isinstance(key, str):
            key = key.encode()
        cipher = Fernet(key)
        return True, "✅ ENCRYPTION_KEY is valid Fernet key"
    except Exception as e:
        return False, f"❌ ENCRYPTION_KEY is invalid: {e}"


def validate_mongodb_url() -> Tuple[bool, str]:
    """Validate MongoDB connection string."""
    url = os.getenv("MONGO_URL")
    
    if not url:
        return True, "⚠️  MONGO_URL not set - using default localhost:27017"
    
    if url == "mongodb://localhost:27017":
        return True, "⚠️  MONGO_URL uses default localhost (OK for dev, NOT for production)"
    
    if "mongodb://" in url or "mongodb+srv://" in url:
        # Don't log the actual URL (may contain credentials)
        if "@" in url:
            return True, "✅ MONGO_URL is set with authentication"
        else:
            return True, "⚠️  MONGO_URL is set without authentication"
    
    return False, "❌ MONGO_URL format is invalid"


def validate_environment(strict_mode: bool = False) -> bool:
    """
    Validate all critical environment variables.
    
    Args:
        strict_mode: If True, fail on warnings. If False, only fail on errors.
    
    Returns:
        True if validation passes, False otherwise
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}🔐 Environment Variable Validation{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    errors: List[str] = []
    warnings: List[str] = []
    success: List[str] = []
    
    # Critical variables (MUST be set)
    critical_vars = [
        ("ENCRYPTION_KEY", validate_encryption_key),
    ]
    
    # Required variables for production
    required_vars = [
        "EMERGENT_LLM_KEY",
        "MONGO_URL",
    ]
    
    # Optional but recommended variables
    optional_vars = [
        "KRAKEN_API_KEY",
        "KRAKEN_API_SECRET",
        "RESEND_API_KEY",
        "ALERT_EMAIL",
        "COINMARKETCAP_API_KEY",
        "CRYPTOPANIC_API_KEY",
    ]
    
    print(f"{Colors.BOLD}Critical Variables:{Colors.RESET}")
    for var_name, validator in critical_vars:
        is_valid, message = validator()
        if is_valid:
            print(f"  {Colors.GREEN}{message}{Colors.RESET}")
            success.append(message)
        else:
            print(f"  {Colors.RED}{message}{Colors.RESET}")
            errors.append(message)
    
    print(f"\n{Colors.BOLD}Required Variables:{Colors.RESET}")
    for var_name in required_vars:
        if var_name == "MONGO_URL":
            is_valid, message = validate_mongodb_url()
        else:
            is_valid, message = validate_env_var(var_name, required=True)
        
        if is_valid:
            if "⚠️" in message:
                print(f"  {Colors.YELLOW}{message}{Colors.RESET}")
                warnings.append(message)
            else:
                print(f"  {Colors.GREEN}{message}{Colors.RESET}")
                success.append(message)
        else:
            print(f"  {Colors.RED}{message}{Colors.RESET}")
            errors.append(message)
    
    print(f"\n{Colors.BOLD}Optional Variables:{Colors.RESET}")
    for var_name in optional_vars:
        is_valid, message = validate_env_var(var_name, required=False)
        if "❌" in message:
            print(f"  {Colors.RED}{message}{Colors.RESET}")
            errors.append(message)
        elif "⚠️" in message:
            print(f"  {Colors.YELLOW}{message}{Colors.RESET}")
            warnings.append(message)
        else:
            print(f"  {Colors.GREEN}{message}{Colors.RESET}")
            success.append(message)
    
    # Summary
    print(f"\n{Colors.BOLD}Summary:{Colors.RESET}")
    print(f"  {Colors.GREEN}✅ Success: {len(success)}{Colors.RESET}")
    print(f"  {Colors.YELLOW}⚠️  Warnings: {len(warnings)}{Colors.RESET}")
    print(f"  {Colors.RED}❌ Errors: {len(errors)}{Colors.RESET}")
    
    # Recommendations
    if warnings or errors:
        print(f"\n{Colors.BOLD}Recommendations:{Colors.RESET}")
        if not os.getenv("ENCRYPTION_KEY"):
            print(f"  {Colors.YELLOW}1. Set ENCRYPTION_KEY to secure stored credentials{Colors.RESET}")
            print(f"     Generate: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
        if not os.getenv("EMERGENT_LLM_KEY") or "placeholder" in os.getenv("EMERGENT_LLM_KEY", "").lower():
            print(f"  {Colors.YELLOW}2. Set EMERGENT_LLM_KEY for AI strategy generation{Colors.RESET}")
        if os.getenv("CORS_ORIGINS") == "*":
            print(f"  {Colors.YELLOW}3. Restrict CORS_ORIGINS in production (currently allows all origins){Colors.RESET}")
        print(f"  {Colors.YELLOW}4. Copy .env.example to .env and fill in your credentials{Colors.RESET}")
        print(f"  {Colors.YELLOW}5. See SECURITY.md for detailed security guidelines{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    # Determine pass/fail
    if errors:
        print(f"{Colors.RED}{Colors.BOLD}❌ Validation FAILED - {len(errors)} critical error(s){Colors.RESET}")
        return False
    
    if strict_mode and warnings:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Validation FAILED in strict mode - {len(warnings)} warning(s){Colors.RESET}")
        return False
    
    if warnings:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Validation PASSED with {len(warnings)} warning(s){Colors.RESET}")
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Validation PASSED - All checks successful!{Colors.RESET}")
    
    return True


if __name__ == "__main__":
    # Check if strict mode is requested
    strict = "--strict" in sys.argv
    
    # Run validation
    success = validate_environment(strict_mode=strict)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
