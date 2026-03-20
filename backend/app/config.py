from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/touhon_db"
    backend_secret_key: str = "change-me"
    cors_origins: str = "http://localhost:3000"

    anthropic_api_key: str = ""
    google_application_credentials: str = ""
    gcs_bucket_name: str = ""

    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60

    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 8

    class Config:
        env_file = ".env"


settings = Settings()
