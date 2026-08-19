from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "JobPulse"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./jobpulse.db"
    LOG_LEVEL: str = "INFO"
    FETCH_INTERVAL_MINUTES: int = 30
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT_SECONDS: int = 10
    REMOTE_SOURCE_URL: str = "https://remotive.com/api/remote-jobs"
    GEMINI_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
