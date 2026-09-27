from sqlalchemy import inspect, text


def ensure_runtime_schema(engine):
    if engine.dialect.name != "postgresql":
        # This helper exists to incrementally patch an already-deployed
        # Postgres database with new columns/tables (it uses
        # Postgres-only DDL like SERIAL and "ADD COLUMN IF NOT EXISTS").
        # Any other dialect (SQLite in tests/local dev) already gets a
        # fully up-to-date schema from Base.metadata.create_all(), so
        # there is nothing for this function to do there.
        return
    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        if "buildings" in tables:
            columns = {column["name"] for column in inspector.get_columns("buildings")}
            additions = {
                "climate_zone": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS climate_zone TEXT DEFAULT 'moderate_dry'",
                "ideal_e2": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS ideal_e2 FLOAT",
                "owner_id": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
                "latitude": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS latitude FLOAT",
                "longitude": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS longitude FLOAT",
                "wall_area_m2": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS wall_area_m2 FLOAT",
                "roof_area_m2": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS roof_area_m2 FLOAT",
                "floor_area_m2": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS floor_area_m2 FLOAT",
                "window_area_m2": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS window_area_m2 FLOAT",
                "wall_material_key": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS wall_material_key TEXT",
                "roof_material_key": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS roof_material_key TEXT",
                "floor_material_key": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS floor_material_key TEXT",
                "window_material_key": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS window_material_key TEXT",
                "airtightness": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS airtightness TEXT DEFAULT 'medium'",
            }
            for column, statement in additions.items():
                if column not in columns:
                    connection.execute(text(statement))
        if "weather_data" in tables:
            columns = {column["name"] for column in inspector.get_columns("weather_data")}
            additions = {
                "humidity": "ALTER TABLE weather_data ADD COLUMN IF NOT EXISTS humidity FLOAT",
                "solar_radiation": "ALTER TABLE weather_data ADD COLUMN IF NOT EXISTS solar_radiation FLOAT",
                "rainfall": "ALTER TABLE weather_data ADD COLUMN IF NOT EXISTS rainfall FLOAT",
                "wind_speed": "ALTER TABLE weather_data ADD COLUMN IF NOT EXISTS wind_speed FLOAT",
            }
            for column, statement in additions.items():
                if column not in columns:
                    connection.execute(text(statement))
        if "audit_results" in tables:
            columns = {column["name"] for column in inspector.get_columns("audit_results")}
            additions = {
                "energy_index_ratio": "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS energy_index_ratio FLOAT",
                "ideal_e2": "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ideal_e2 FLOAT",
                "climate_zone": "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS climate_zone TEXT",
                "theoretical_heating_mj": "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS theoretical_heating_mj FLOAT",
                "theoretical_cooling_mj": "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS theoretical_cooling_mj FLOAT",
                "envelope_diagnosis": "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS envelope_diagnosis TEXT",
                "total_co2_kg": "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS total_co2_kg FLOAT",
                "performance_score": "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS performance_score INTEGER",
            }
            for column, statement in additions.items():
                if column not in columns:
                    connection.execute(text(statement))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS electric_equipment (
                id SERIAL PRIMARY KEY,
                building_id INT REFERENCES buildings(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                category TEXT,
                quantity FLOAT DEFAULT 1,
                power_w FLOAT DEFAULT 0,
                hours_per_day FLOAT DEFAULT 0,
                days_per_year FLOAT DEFAULT 365,
                usage_period TEXT
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS gas_equipment (
                id SERIAL PRIMARY KEY,
                building_id INT REFERENCES buildings(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                category TEXT,
                quantity FLOAT DEFAULT 1,
                gas_m3_per_hour FLOAT DEFAULT 0,
                hours_per_day FLOAT DEFAULT 0,
                days_per_year FLOAT DEFAULT 365,
                usage_period TEXT
            )
        """))
