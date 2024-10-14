from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_HOST_WRITE: str
    DATABASE_HOST_READ: str
    DATABASE_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_TEST_FP: str
    ENVIRONMENT: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_WARNING_MINS: int

    MIDDLEWARE_SECRET_KEY: str

    ESDB_CONNECTION_STRING: str

    LOG_LEVEL: str


settings = Settings()  # type: ignore
