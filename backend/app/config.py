from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------
    app_name: str = "Baytak Foundation API"
    environment: str = "development"

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "charity"
    database_user: str = "charity"
    database_password: str = "charity"

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}"
            f"/{self.database_name}"
        )

    # -------------------------------------------------------------------------
    # JWT
    # -------------------------------------------------------------------------
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"

    access_token_minutes: int = 30
    refresh_token_days: int = 30

    # -------------------------------------------------------------------------
    # Bootstrap admin
    # -------------------------------------------------------------------------
    bootstrap_admin_email: str
    bootstrap_admin_password: str

    # -------------------------------------------------------------------------
    # Frontend
    # -------------------------------------------------------------------------
    frontend_app_url: str = "http://localhost:3000"

    allowed_origins: list[str] = Field(
        default=["*"],
        alias="ALLOWED_ORIGINS",
    )

    # -------------------------------------------------------------------------
    # Password reset
    # -------------------------------------------------------------------------
    password_reset_minutes: int = 30

    # -------------------------------------------------------------------------
    # Email
    # -------------------------------------------------------------------------
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_starttls: bool = True

    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # -------------------------------------------------------------------------
    # Scheduler
    # -------------------------------------------------------------------------
    scheduler_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


    report_storage_path: str = Field(
        default="/app/reports",
        alias="REPORT_STORAGE_PATH",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

# from functools import lru_cache

# from pydantic import Field, computed_field
# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     app_name: str = "Baytak Foundation API"
#     environment: str = "development"

#     database_host: str = "localhost"
#     database_port: int = 5432
#     database_name: str = "charity"
#     database_user: str = "charity"
#     database_password: str = "charity"

#     bootstrap_admin_email: str
#     bootstrap_admin_password: str

    
#     @computed_field
#     @property
#     def database_url(self) -> str:
#         return (
#             f"postgresql+psycopg://"
#             f"{self.database_user}:{self.database_password}"
#             f"@{self.database_host}:{self.database_port}/"
#             f"{self.database_name}"
#         )

#     allowed_origins: list[str] = Field(
#         default=["*"],
#         alias="ALLOWED_ORIGINS",
#     )

#     jwt_secret_key: str = Field(..., min_length=32)

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         extra="ignore",
#     )


# @lru_cache
# def get_settings() -> Settings:
#     return Settings()