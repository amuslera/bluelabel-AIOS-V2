"""
Simple configuration validation without runtime checks.
"""
import sys
from typing import List, Tuple

from core.config_fixed import get_settings


def validate_config_on_startup():
    """
    Validate configuration when the application starts.
    Skip runtime dependency checks for development.
    """
    try:
        settings = get_settings()
        print(f"Configuration loaded successfully")
        print(f"  Debug mode: {settings.debug}")
        print(f"  Log level: {settings.logging.level}")
        print(f"  Redis simulation: {settings.REDIS_SIMULATION_MODE}")
        print(f"  LLM enabled: {settings.LLM_ENABLED}")
        
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)