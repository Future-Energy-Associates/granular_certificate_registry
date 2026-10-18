import logging
import os
from typing import Any

from google.cloud import secretmanager
from pydantic_settings import BaseSettings, SettingsConfigDict

_secret_cache: dict[str, Any] = {}


def get_secret(secret_name: str) -> str | None:
    """
    Fetches a secret from Google Cloud Secret Manager.
    Implements caching to avoid repeated API calls for the same secret.
    """
    if secret_name in _secret_cache:
        logging.debug(f"Using cached value for secret: {secret_name}")
        return _secret_cache[secret_name]

    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

        if not project_id:
            logging.error("GOOGLE_CLOUD_PROJECT environment variable not set")
            return None

        secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        logging.info(f"Attempting to access secret: {secret_name}")

        response = client.access_secret_version(name=secret_path)
        secret_value = response.payload.data.decode("UTF-8")

        _secret_cache[secret_name] = secret_value

        logging.info(f"Successfully retrieved secret: {secret_name}")
        return secret_value

    except Exception as e:
        logging.error(f"Error fetching secret {secret_name}: {e}")
        return None


_DEFAULT_SIGNING_KEY = "secret_key"


class ProductionConfigurationError(RuntimeError):
    """Raised when AWS production is missing a real signing key."""


def uses_gcp_secret_manager() -> bool:
    """Return whether this process should load Google Secret Manager.

    Cloud Run sets ``GOOGLE_CLOUD_PROJECT``. AWS tasks leave it unset and
    supply configuration in the environment instead.

    Returns:
        True when the GCP project environment variable is non-empty.
    """
    return bool(os.getenv("GOOGLE_CLOUD_PROJECT", "").strip())


def require_aws_signing_keys(jwt_secret: str | None, middleware_secret: str | None) -> None:
    """Refuse to start AWS production with a missing or default signing key.

    Args:
        jwt_secret: Value that will sign access tokens.
        middleware_secret: Value that will sign the session cookie.

    Raises:
        ProductionConfigurationError: Either key is missing or still the
            built-in default.
    """
    if not jwt_secret or jwt_secret == _DEFAULT_SIGNING_KEY:
        raise ProductionConfigurationError(
            "JWT_SECRET_KEY must be set to a non-default value in production"
        )
    if not middleware_secret or middleware_secret == _DEFAULT_SIGNING_KEY:
        raise ProductionConfigurationError(
            "MIDDLEWARE_SECRET_KEY must be set to a non-default value in production"
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "CI")

    # Define all secrets as optional initially
    DATABASE_HOST_READ: str | None = None
    DATABASE_HOST_WRITE: str | None = None
    GCP_INSTANCE_READ: str | None = None
    GCP_INSTANCE_WRITE: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    ESDB_CONNECTION_STRING: str | None = None
    FRONTEND_URL: str | None = "localhost:9000"
    JWT_SECRET_KEY: str = _DEFAULT_SIGNING_KEY
    JWT_ALGORITHM: str = "HS256"
    MIDDLEWARE_SECRET_KEY: str = _DEFAULT_SIGNING_KEY

    # Other configuration
    DATABASE_PORT: int = 5432
    POSTGRES_DB: str = "registry"
    CERTIFICATE_GRANULARITY_HOURS: float = 1
    CERTIFICATE_EXPIRY_YEARS: int = 2
    CAPACITY_MARGIN: float = 1.1
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    API_KEY_EXPIRE_DAYS: int = 365
    API_KEY_MAX_EXPIRE_DAYS: int = 1095  # 3 years
    REFRESH_WARNING_MINS: int = 5
    LOG_LEVEL: str = "INFO"
    PROFILING_ENABLED: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.ENVIRONMENT == "PROD" and uses_gcp_secret_manager():
            try:
                self.DATABASE_HOST_READ = get_secret("DATABASE_HOST_READ")
                self.DATABASE_HOST_WRITE = get_secret("DATABASE_HOST_WRITE")
                self.GCP_INSTANCE_READ = get_secret("GCP_INSTANCE_READ")
                self.GCP_INSTANCE_WRITE = get_secret("GCP_INSTANCE_WRITE")
                self.POSTGRES_USER = get_secret("POSTGRES_USER")
                self.POSTGRES_PASSWORD = get_secret("POSTGRES_PASSWORD")
                self.ESDB_CONNECTION_STRING = get_secret("ESDB_CONNECTION_STRING")
                self.FRONTEND_URL = get_secret("FRONTEND_URL")
                self.JWT_SECRET_KEY = get_secret("JWT_SECRET_KEY")
                self.JWT_ALGORITHM = get_secret("JWT_ALGORITHM")
                self.MIDDLEWARE_SECRET_KEY = get_secret("MIDDLEWARE_SECRET_KEY")
            except Exception as e:
                logging.error(f"Error fetching secret: {e}")
        elif self.ENVIRONMENT == "PROD":
            require_aws_signing_keys(self.JWT_SECRET_KEY, self.MIDDLEWARE_SECRET_KEY)


settings = Settings()
