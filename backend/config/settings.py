from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
    
    # Spanner Settings (aliased for compatibility with both existing and new code expectations)
    INSTANCE_ID: str = "survivor-network"  # Default from user req "survivor-network", was "your-instance-id"
    SPANNER_INSTANCE_ID: Optional[str] = None # Will default to INSTANCE_ID in __init__ if not set
    
    DATABASE_ID: str = "graph-db" # Default from user req "graph-db", was "your-database-id"
    SPANNER_DATABASE_ID: Optional[str] = None # Will default to DATABASE_ID
    
    GRAPH_NAME: str = "SurvivorNetwork" # User requested "SurvivorNetwork"
    
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Vertex AI & Memory Bank
    LOCATION: str = "us-central1"
    AGENT_ENGINE_ID: Optional[str] = None
    GCS_BUCKET_NAME: str = "survivor-network-media" # Default
    USE_MEMORY_BANK: bool = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.SPANNER_INSTANCE_ID:
            self.SPANNER_INSTANCE_ID = self.INSTANCE_ID
        if not self.SPANNER_DATABASE_ID:
            self.SPANNER_DATABASE_ID = self.DATABASE_ID

    class Config:
        # Resolve .env file relative to this file (backend/config/settings.py -> ../../.env)
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        env_file = env_path
        extra = "ignore"

settings = Settings()
