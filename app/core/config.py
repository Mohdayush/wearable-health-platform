from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./health.db"
    jwt_secret: SecretStr = SecretStr("dev-only-change-me")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    influx_url: str | None = None
    influx_token: SecretStr | None = None
    influx_org: str = "pulsepath"
    influx_bucket: str = "vitals"
    app_env: str = "development"


settings = Settings()
