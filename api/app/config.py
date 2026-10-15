from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-change-me"
    DATABASE_URL: str = "sqlite:///./fidelizacion.db"
    REDIS_URL: str = ""
    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    OTP_TTL_SECONDS: int = 300
    QR_TTL_SECONDS: int = 300
    CORS_ORIGINS: str = "*"
    API_PREFIX: str = "/fid-api"
    SYNC_API_KEY: str = "dev-api-key"

    @property
    def cors_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
