from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    cors_allow_origins: tuple[str, ...] = ("http://localhost:5173",)
    database_url: str = "postgresql+asyncpg://appuser:apppassword@postgres:5432/appdb"


def get_settings() -> Settings:
    return Settings()
