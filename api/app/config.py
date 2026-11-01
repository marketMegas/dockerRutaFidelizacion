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
    OTP_IP_RATE_MAX: int = 30
    IDENT_IP_RATE_MAX: int = 60
    ADMIN_RATE_MAX: int = 10
    ADMIN_RATE_VENTANA: int = 900
    ISLERO_RATE_MAX: int = 10
    ISLERO_RATE_VENTANA: int = 900
    SYNC_RATE_MAX: int = 1200
    SYNC_RATE_VENTANA: int = 60
    CORS_ORIGINS: str = ""
    API_PREFIX: str = "/fid-api"
    SYNC_API_KEY: str = "dev-api-key"
    SMS_PROVIDER: str = "debug"
    SMS_API_URL: str = ""
    SMS_API_KEY: str = ""
    SMS_FROM: str = "FidelizacionGLP"
    CATALOGO_PATH: str = "/app/data/catalogo.json"
    TZ_ESTACION: str = "America/Bogota"
    ASISTENTE_RATE_MAX: int = 20
    ASISTENTE_RATE_VENTANA: int = 60
    ASISTENTE_LLM_ENABLED: bool = False
    ASISTENTE_LLM_BASE_URL: str = "https://api.openai.com/v1"
    ASISTENTE_LLM_API_KEY: str = ""
    ASISTENTE_LLM_MODEL: str = ""
    ASISTENTE_LLM_TIMEOUT: int = 15
    ASISTENTE_LLM_MAX_TOKENS: int = 400

    @property
    def cors_list(self) -> list[str]:
        # Sin origenes configurados no se permite ninguno (deny por defecto).
        if self.CORS_ORIGINS.strip() in {"", "*"}:
            return [] if self.CORS_ORIGINS.strip() == "" else ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
