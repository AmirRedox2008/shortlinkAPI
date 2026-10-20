from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./shortener.db"
    base_url: str = "http://localhost:8000"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600       
    rate_limit: int = 20         
    rate_limit_window: int = 60 

settings = Settings()