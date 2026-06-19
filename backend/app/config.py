from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_allow_origins: tuple[str, ...] = Field(
        default=("http://localhost:5173",),
        validation_alias=AliasChoices("APP_CORS_ALLOW_ORIGINS", "CORS_ALLOW_ORIGINS"),
    )
    database_url: str = Field(
        default=(
            "mssql+aioodbc://appuser:AppPassword%212026@mssql:1433/appdb"
            "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        ),
        validation_alias=AliasChoices("APP_DATABASE_URL", "DATABASE_URL"),
    )


def get_settings() -> Settings:
    return Settings()
