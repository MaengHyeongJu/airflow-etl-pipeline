from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    datamart_reader_dsn: str = "postgresql://dashboard_reader:dashboard_reader_pw@localhost:5432/datamart"
    backend_cors_origins: str = "http://localhost:5173,http://localhost:8081"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


settings = Settings()
