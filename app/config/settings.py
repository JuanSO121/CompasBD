from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_NAME: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str
    FROM_NAME: str

    ALLOWED_ORIGINS: List[str]

    BCRYPT_ROUNDS: int
    MAX_LOGIN_ATTEMPTS: int
    LOCKOUT_DURATION_MINUTES: int

    REDIS_URL: str
    USE_REDIS: bool

    FRONTEND_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
