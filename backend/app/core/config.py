from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict # type: ignore


class Settings(BaseSettings):
    APP_NAME: str = "Nova AI CRM"

    GROQ_API_KEY: str

    MODEL_NAME: str = "openai/gpt-oss-120b"

    DATABASE_URL: str = "sqlite:///./novacare.db"
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "ai_crm"
    MYSQL_USER: str = "crm_user"
    MYSQL_PASSWORD: str = "crm_password"

    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_USE_TLS: bool = True

    model_config = SettingsConfigDict(
        env_file=(".env", "/etc/secrets/.env"),
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()