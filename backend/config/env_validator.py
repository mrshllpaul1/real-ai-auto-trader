"""
Environment Variable Validator
Validates required environment variables on application startup
Prevents runtime errors due to missing configuration
"""

import os
import logging
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class EnvVarType(Enum):
    """Environment variable types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    URL = "url"
    PATH = "path"


class EnvVarConfig:
    """Environment variable configuration"""
    
    def __init__(
        self,
        name: str,
        required: bool = False,
        var_type: EnvVarType = EnvVarType.STRING,
        default: Optional[Any] = None,
        description: str = "",
        validation_func: Optional[callable] = None
    ):
        self.name = name
        self.required = required
        self.var_type = var_type
        self.default = default
        self.description = description
        self.validation_func = validation_func


# Define all environment variables used by the application
ENV_VARS = [
    # Database
    EnvVarConfig(
        "MONGODB_URL",
        required=True,
        var_type=EnvVarType.URL,
        description="MongoDB connection URL"
    ),
    EnvVarConfig(
        "MONGODB_DB_NAME",
        required=True,
        var_type=EnvVarType.STRING,
        default="crypto_trading",
        description="MongoDB database name"
    ),
    
    # API Keys
    EnvVarConfig(
        "OPENAI_API_KEY",
        required=False,
        var_type=EnvVarType.STRING,
        description="OpenAI API key for AI strategy generation"
    ),
    EnvVarConfig(
        "EMERGENT_LLM_KEY",
        required=False,
        var_type=EnvVarType.STRING,
        description="Emergent LLM API key"
    ),
    
    # Application Settings
    EnvVarConfig(
        "CORS_ORIGINS",
        required=False,
        var_type=EnvVarType.STRING,
        default="*",
        description="Comma-separated list of allowed CORS origins"
    ),
    EnvVarConfig(
        "LOG_LEVEL",
        required=False,
        var_type=EnvVarType.STRING,
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    ),
    EnvVarConfig(
        "PORT",
        required=False,
        var_type=EnvVarType.INTEGER,
        default=8001,
        description="Server port"
    ),
    
    # ML/AI Settings
    EnvVarConfig(
        "ENABLE_ML_TRAINING",
        required=False,
        var_type=EnvVarType.BOOLEAN,
        default=False,
        description="Enable ML model training"
    ),
    EnvVarConfig(
        "ML_LIGHTWEIGHT_MODE",
        required=False,
        var_type=EnvVarType.BOOLEAN,
        default=True,
        description="Use lightweight ML mode for deployment"
    ),
    EnvVarConfig(
        "MAX_TRAINING_EPOCHS",
        required=False,
        var_type=EnvVarType.INTEGER,
        default=10,
        description="Maximum training epochs for ML models"
    ),
    
    # Trading Settings
    EnvVarConfig(
        "PAPER_TRADING_MODE",
        required=False,
        var_type=EnvVarType.BOOLEAN,
        default=True,
        description="Enable paper trading mode by default"
    ),
    EnvVarConfig(
        "MAX_POSITION_SIZE_USD",
        required=False,
        var_type=EnvVarType.FLOAT,
        default=1000.0,
        description="Maximum position size in USD"
    ),
]


class ValidationResult:
    """Result of environment validation"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.values: Dict[str, Any] = {}
    
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return len(self.errors) == 0
    
    def add_error(self, message: str):
        """Add error message"""
        self.errors.append(message)
        logger.error(f"ENV VALIDATION ERROR: {message}")
    
    def add_warning(self, message: str):
        """Add warning message"""
        self.warnings.append(message)
        logger.warning(f"ENV VALIDATION WARNING: {message}")
    
    def add_info(self, message: str):
        """Add info message"""
        self.info.append(message)
        logger.info(f"ENV VALIDATION INFO: {message}")
    
    def summary(self) -> str:
        """Get validation summary"""
        lines = ["Environment Variable Validation Summary:", "=" * 50]
        
        if self.errors:
            lines.append(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  - {error}")
        
        if self.warnings:
            lines.append(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        if self.info:
            lines.append(f"\n✅ INFO ({len(self.info)}):")
            for info in self.info:
                lines.append(f"  - {info}")
        
        lines.append("\n" + "=" * 50)
        return "\n".join(lines)


def parse_value(value: str, var_type: EnvVarType) -> Any:
    """Parse environment variable value based on type"""
    if var_type == EnvVarType.STRING:
        return value
    elif var_type == EnvVarType.INTEGER:
        return int(value)
    elif var_type == EnvVarType.FLOAT:
        return float(value)
    elif var_type == EnvVarType.BOOLEAN:
        return value.lower() in ('true', '1', 'yes', 'on')
    elif var_type == EnvVarType.URL:
        return value
    elif var_type == EnvVarType.PATH:
        return value
    return value


def validate_environment() -> ValidationResult:
    """
    Validate all environment variables
    Returns ValidationResult with errors, warnings, and parsed values
    """
    result = ValidationResult()
    
    for var_config in ENV_VARS:
        value = os.environ.get(var_config.name)
        
        # Check if required variable is missing
        if var_config.required and not value:
            if var_config.default is not None:
                result.add_warning(
                    f"{var_config.name} not set, using default: {var_config.default}"
                )
                result.values[var_config.name] = var_config.default
            else:
                result.add_error(
                    f"Required environment variable {var_config.name} is not set. "
                    f"Description: {var_config.description}"
                )
            continue
        
        # Use default if not set
        if not value:
            if var_config.default is not None:
                result.values[var_config.name] = var_config.default
                result.add_info(
                    f"{var_config.name} using default: {var_config.default}"
                )
            continue
        
        # Parse and validate value
        try:
            parsed_value = parse_value(value, var_config.var_type)
            
            # Run custom validation if provided
            if var_config.validation_func:
                is_valid, error_msg = var_config.validation_func(parsed_value)
                if not is_valid:
                    result.add_error(
                        f"{var_config.name} validation failed: {error_msg}"
                    )
                    continue
            
            result.values[var_config.name] = parsed_value
            result.add_info(f"{var_config.name} = {parsed_value}")
            
        except (ValueError, TypeError) as e:
            result.add_error(
                f"{var_config.name} has invalid value '{value}' for type {var_config.var_type.value}: {str(e)}"
            )
    
    return result


def validate_and_exit_on_error():
    """
    Validate environment variables and exit if critical errors found
    This should be called at application startup
    """
    logger.info("Validating environment variables...")
    result = validate_environment()
    
    # Print summary
    print(result.summary())
    
    # Exit if there are errors
    if not result.is_valid():
        logger.critical("Environment validation failed! Application cannot start.")
        raise SystemExit(1)
    
    logger.info("Environment validation passed ✅")
    return result.values


def get_env_config() -> Dict[str, Any]:
    """Get validated environment configuration"""
    result = validate_environment()
    if not result.is_valid():
        logger.error("Environment validation has errors, but continuing...")
    return result.values
