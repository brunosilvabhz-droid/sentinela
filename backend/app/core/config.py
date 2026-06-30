from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SENTINELA"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://sentinela:sentinela@localhost:5432/sentinela"
    redis_url: str = "redis://localhost:6379/0"
    cors_allowed_origins: str = ""
    frontend_public_url: str = "http://localhost:5180"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    smtp_host: str = ""
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "alerts@sentinela.local"
    whatsapp_provider: str = "meta"
    meta_whatsapp_token: str = ""
    meta_whatsapp_phone_number_id: str = ""
    meta_whatsapp_api_version: str = "v20.0"
    meta_whatsapp_template_name: str = ""
    meta_whatsapp_template_language: str = "pt_BR"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    max_alerts_free_plan: int = 5
    default_max_upload_mb: int = 10
    default_data_retention_days: int = 90
    max_ingestion_batch_records: int = 5000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def parse_cors_origins(origins: str) -> list[str]:
    return [origin.strip() for origin in origins.split(",") if origin.strip()]
