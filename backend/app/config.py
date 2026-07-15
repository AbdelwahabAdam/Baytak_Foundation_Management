from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Baytak Foundation API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://charity:charity@localhost:5432/charity"
    jwt_secret_key: str = Field(
        "change-this-local-development-secret-before-production",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    password_reset_minutes: int = 30
    cors_origins: str = "http://localhost:5173,http://localhost:4173"
    frontend_app_url: str = "http://localhost:8080"
    bootstrap_admin_email: str = "admin@charity.local"
    bootstrap_admin_password: str = "ChangeMe123!"
    report_storage_path: str = "reports"
    scheduler_enabled: bool = True
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
