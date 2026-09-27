CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    project_name TEXT NOT NULL,
    city TEXT DEFAULT 'جاجرم',
    address TEXT,
    area_m2 FLOAT NOT NULL CHECK (area_m2 > 0),
    floors INT,
    year_built INT,
    occupants INT NOT NULL CHECK (occupants > 0),
    building_type TEXT DEFAULT 'Residential',
    heating_system TEXT,
    cooling_system TEXT,
    lighting_type TEXT,
    window_type TEXT,
    wall_type TEXT,
    roof_type TEXT,
    climate_zone TEXT DEFAULT 'moderate_dry',
    ideal_e2 FLOAT,
    has_insulation BOOLEAN DEFAULT FALSE,
    has_thermostat BOOLEAN DEFAULT FALSE,
    has_shading BOOLEAN DEFAULT FALSE,
    orientation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE energy_bills (
    id SERIAL PRIMARY KEY,
    building_id INT REFERENCES buildings(id) ON DELETE CASCADE,
    year INT NOT NULL,
    month INT NOT NULL CHECK (month BETWEEN 1 AND 12),
    electricity_kwh FLOAT DEFAULT 0 CHECK (electricity_kwh >= 0),
    gas_m3 FLOAT DEFAULT 0 CHECK (gas_m3 >= 0),
    electricity_cost FLOAT,
    gas_cost FLOAT,
    UNIQUE (building_id, year, month)
);

CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    building_id INT REFERENCES buildings(id) ON DELETE CASCADE,
    city TEXT DEFAULT 'جاجرم',
    date DATE NOT NULL,
    temp_min FLOAT,
    temp_max FLOAT,
    temp_avg FLOAT NOT NULL,
    humidity FLOAT,
    solar_radiation FLOAT,
    rainfall FLOAT,
    wind_speed FLOAT,
    UNIQUE (building_id, date)
);

CREATE TABLE audit_results (
    id SERIAL PRIMARY KEY,
    building_id INT REFERENCES buildings(id) ON DELETE CASCADE,
    total_energy_mj FLOAT NOT NULL,
    eui FLOAT NOT NULL,
    energy_per_person FLOAT NOT NULL,
    hdd FLOAT DEFAULT 0,
    cdd FLOAT DEFAULT 0,
    energy_rating TEXT NOT NULL,
    energy_index_ratio FLOAT,
    ideal_e2 FLOAT,
    climate_zone TEXT,
    standard_eui FLOAT NOT NULL,
    high_consumption_flag BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    building_id INT REFERENCES buildings(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    impact_level TEXT NOT NULL,
    status TEXT DEFAULT 'planned'
);

CREATE TABLE electric_equipment (
    id SERIAL PRIMARY KEY,
    building_id INT REFERENCES buildings(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT,
    quantity FLOAT DEFAULT 1,
    power_w FLOAT DEFAULT 0,
    hours_per_day FLOAT DEFAULT 0,
    days_per_year FLOAT DEFAULT 365,
    usage_period TEXT
);

CREATE TABLE gas_equipment (
    id SERIAL PRIMARY KEY,
    building_id INT REFERENCES buildings(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT,
    quantity FLOAT DEFAULT 1,
    gas_m3_per_hour FLOAT DEFAULT 0,
    hours_per_day FLOAT DEFAULT 0,
    days_per_year FLOAT DEFAULT 365,
    usage_period TEXT
);
