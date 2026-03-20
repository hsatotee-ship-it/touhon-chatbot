import json
import os
import tempfile

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/touhon_db"
    backend_secret_key: str = "change-me"
    cors_origins: str = "http://localhost:3000"

    anthropic_api_key: str = ""
    google_application_credentials: str = ""
    google_credentials_json: str = ""
    gcs_bucket_name: str = ""

    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60

    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 8

    class Config:
        env_file = ".env"


settings = Settings()


def _setup_google_credentials():
    """Write GOOGLE_CREDENTIALS_JSON to a temp file and set GOOGLE_APPLICATION_CREDENTIALS."""
    if settings.google_credentials_json and not settings.google_application_credentials:
        try:
            creds = json.loads(settings.google_credentials_json)
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            )
            json.dump(creds, tmp)
            tmp.close()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
            settings.google_application_credentials = tmp.name
        except json.JSONDecodeError:
            pass


_setup_google_credentials()
