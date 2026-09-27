from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Iran Residential Energy Audit Platform"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/energy_audit"
    default_standard_eui_mj_m2_year: float = 324.0
    degree_day_base_temp_c: float = 18.0
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Auth. CHANGE jwt_secret in production (set the JWT_SECRET env var) --
    # the fallback below is only safe for local/dev use.
    jwt_secret: str = "dev-only-insecure-secret-change-me-in-production"

    # Economics defaults. These are editable placeholders -- residential
    # electricity/gas tariffs in Iran are tiered/subsidized, so this
    # represents a single average marginal rate rather than the full
    # tiered schedule; recalibrate before showing a client real numbers.
    electricity_toman_per_kwh: float = 5000.0
    gas_toman_per_m3: float = 3000.0
    grid_emission_factor_kg_co2_per_kwh: float = 0.5
    gas_emission_factor_kg_co2_per_m3: float = 2.0

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
