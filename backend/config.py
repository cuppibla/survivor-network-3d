from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_ID: str = "your-project-id"
    INSTANCE_ID: str = "your-instance-id"
    DATABASE_ID: str = "your-database-id"
    GRAPH_NAME: str = "SurvivorGraph"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Vertex AI & Memory Bank
    PROJECT_ID: Optional[str] = None
    LOCATION: str = "us-central1"
    AGENT_ENGINE_ID: Optional[str] = None
    GCS_BUCKET_NAME: str = "survivor-network-media"
    USE_MEMORY_BANK: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
