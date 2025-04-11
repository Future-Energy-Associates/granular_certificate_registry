import logging
import os

from google.cloud import secretmanager
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_secret(secret_name: str) -> str:
    """
    Fetches a secret from Google Cloud Secret Manager.
    """
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=secret_path)
    return response.payload.data.decode("UTF-8")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "CI")

    # Define all secrets as optional initially
    DATABASE_HOST_READ: str | None = None
    DATABASE_HOST_WRITE: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    ESDB_CONNECTION_STRING: str | None = None
    FRONTEND_URL: str | None = "localhost:9000"

    JWT_SECRET_KEY: str = "secret_key"
    JWT_ALGORITHM: str = "HS256"
    MIDDLEWARE_SECRET_KEY: str = "secret_key"

    # Other configuration
    DATABASE_PORT: int = 5432
    POSTGRES_DB: str = "registry"
    CERTIFICATE_GRANULARITY_HOURS: float = 1
    CERTIFICATE_EXPIRY_YEARS: int = 2
    CAPACITY_MARGIN: float = 1.1
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_WARNING_MINS: int = 5
    LOG_LEVEL: str = "INFO"
    PROFILING_ENABLED: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.ENVIRONMENT == "PROD":
            try:
                self.DATABASE_HOST_READ = get_secret("DATABASE_HOST_READ")
                self.DATABASE_HOST_WRITE = get_secret("DATABASE_HOST_WRITE")
                self.POSTGRES_USER = get_secret("POSTGRES_USER")
                self.POSTGRES_PASSWORD = get_secret("POSTGRES_PASSWORD")
                self.ESDB_CONNECTION_STRING = get_secret("ESDB_CONNECTION_STRING")
                self.FRONTEND_URL = get_secret("FRONTEND_URL")
                self.JWT_SECRET_KEY = get_secret("JWT_SECRET_KEY")
                self.JWT_ALGORITHM = get_secret("JWT_ALGORITHM")
                self.MIDDLEWARE_SECRET_KEY = get_secret("MIDDLEWARE_SECRET_KEY")
            except Exception as e:
                logging.warning(f"Error fetching secret: {e}")


settings = Settings()
