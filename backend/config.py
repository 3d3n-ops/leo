# config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    supabase_url: str
    supabase_anon_key: Optional[str] = None
    supabase_password: Optional[str] = None
    
    # Vector Store
    pinecone_api_key: str
    pinecone_environment: str = "us-east-1"
    pinecone_index: str = "docs-wiki"
    
    # LLM
    groq_api_key: str
    openai_api_key: Optional[str] = None
    
    # Scraping
    max_pages: int = 100
    max_concurrency: int = 10
    rate_limit: float = 0.5
    
    # Task Management
    task_cleanup_interval: int = 300
    task_ttl: int = 3600
    
    class Config:
        env_file = ".env"

settings = Settings()