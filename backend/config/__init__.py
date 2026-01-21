"""
Configuration module for survivor-network-3d backend.
Loads environment variables from .env file using python-dotenv.
"""
import os
from dotenv import load_dotenv

# Load .env from project root (searches parent directories automatically)
load_dotenv()

# Export configuration classes
from .extraction_config import ExtractionConfig, MediaType

__all__ = ['ExtractionConfig', 'MediaType']
