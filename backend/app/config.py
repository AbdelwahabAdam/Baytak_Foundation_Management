from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Baytak Foundation API"
    environment: str = "development"

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
            f"@{self.database_host}:{self.database_port}/"
            f"{self.database_name}"
        )

    allowed_origins: list[str] = Field(
        default=["*"],
        alias="ALLOWED_ORIGINS",
    )

    jwt_secret_key: str = Field(..., min_length=32)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()