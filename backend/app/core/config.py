from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "城策城市治理决策支持平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://cgdss:cgdss123@postgres:5432/cgdss")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Dify API
    DIFY_API_URL: str = os.getenv("DIFY_API_URL", "http://192.168.71.101:8080/v1")
    DIFY_API_KEY: str = os.getenv("DIFY_API_KEY", "")
    DIFY_APP_ID: str = os.getenv("DIFY_APP_ID", "")
    DIFY_DATASET_ID: str = os.getenv("DIFY_DATASET_ID", "")

    # DeepSeek LLM API
    DEEPSEEK_API_URL: str = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cgdss-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
