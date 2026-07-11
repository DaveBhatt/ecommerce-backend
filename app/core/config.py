from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()