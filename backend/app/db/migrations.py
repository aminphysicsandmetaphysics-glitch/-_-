from sqlalchemy import inspect, text


def ensure_runtime_schema(engine):
    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        if "buildings" in tables:
            columns = {column["name"] for column in inspector.get_columns("buildings")}
            additions = {
                "climate_zone": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS climate_zone TEXT DEFAULT 'moderate_dry'",
                "ideal_e2": "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS ideal_e2 FLOAT",
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
