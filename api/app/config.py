import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DEBUG: bool = False
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    DATABASE_URL: str = "sqlite:///./fidelizacion.db"
    REDIS_URL: str = ""
    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    OTP_TTL_SECONDS: int = 300
    OTP_RATE_MAX: int = 5
    OTP_RATE_VENTANA: int = 900
    ADMIN_RATE_MAX: int = 10
    ADMIN_RATE_VENTANA: int = 900
    CORS_ORIGINS: str = "*"
    API_PREFIX: str = "/fid-api"
    SYNC_API_KEY: str = "dev-api-key"
    SMS_PROVIDER: str = "debug"
    SMS_API_URL: str = ""
    SMS_API_KEY: str = ""
    SMS_FROM: str = "FidelizacionGLP"

    @property
    def cors_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
