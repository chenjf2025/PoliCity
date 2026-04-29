from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "城策城市治理决策支持平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://cgdss:cgdss123@postgres:5432/cgdss"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Dify API
    DIFY_API_URL: str = "http://192.168.71.101:8080/v1"
    DIFY_API_KEY: str = "app-drScqCHbwG0oUmh2TYqr6lnT"
    DIFY_APP_ID: str = "46f69385-1556-4107-80f7-e0b0424a63cc"
    DIFY_DATASET_ID: str = "f14f5c44-d420-442e-adaa-bf8c8887e75b"

    # DeepSeek LLM API
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_API_KEY: str = "sk-3edb33a0774d45f789feaa2bd18acb56"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Security
    SECRET_KEY: str = "cgdss-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
