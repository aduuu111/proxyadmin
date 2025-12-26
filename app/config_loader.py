"""
Configuration loader for core service settings.
"""
import configparser
import os
from pathlib import Path


def load_core_config():
    """Load core service configuration from core_config.ini"""
    config = configparser.ConfigParser()

    # Try to find config file
    config_paths = [
        Path(__file__).parent.parent / "core_config.ini",  # Project root
        Path("/etc/proxyadmin/core_config.ini"),  # System config
        Path.home() / ".proxyadmin" / "core_config.ini"  # User config
    ]

    config_file = None
    for path in config_paths:
        if path.exists():
            config_file = path
            break

    if config_file:
        config.read(config_file)
        return {
            "api_url": config.get("core_service", "api_url", fallback="http://127.0.0.1:8080"),
            "api_key": config.get("core_service", "api_key", fallback=""),
            "timeout": config.getfloat("core_service", "timeout", fallback=10.0)
        }

    # Fallback to environment variables
    return {
        "api_url": os.getenv("CORE_API_URL", "http://127.0.0.1:8080"),
        "api_key": os.getenv("CORE_API_KEY", ""),
        "timeout": float(os.getenv("CORE_API_TIMEOUT", "10.0"))
    }
