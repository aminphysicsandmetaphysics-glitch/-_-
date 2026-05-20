from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Iran Residential Energy Audit Platform"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/energy_audit"
    default_standard_eui_mj_m2_year: float = 324.0
    degree_day_base_temp_c: float = 18.0
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    class Config:
        env_file = ".env"


settings = Settings()
