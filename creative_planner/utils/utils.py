import os
from typing import Optional

def get_required_env_var(name: str, default: Optional[str] = None) -> str:
    """Get a required environment variable or raise an exception if not found."""
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Required environment variable {name} is not set")
    return value 