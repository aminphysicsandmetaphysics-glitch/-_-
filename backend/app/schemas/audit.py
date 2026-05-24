from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BuildingBase(BaseModel):
    project_name: str
    city: str = "جاجرم"
    address: str | None = None
    area_m2: float = Field(gt=0)
    floors: int | None = None
    year_built: int | None = None
    occupants: int = Field(gt=0)
    building_type: str = "Residential"
    heating_system: str | None = None
    cooling_system: str | None = None
    lighting_type: str | None = None
    window_type: str | None = None
    wall_type: str | None = None
    roof_type: str | None = None
    climate_zone: str | None = "moderate_dry"
    ideal_e2: float | None = None
    has_insulation: bool = False
    has_thermostat: bool = False
    has_shading: bool = False
    orientation: str | None = None


class BuildingCreate(BuildingBase):
    pass


class BuildingRead(BuildingBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EnergyBillBase(BaseModel):
    year: int
    month: int = Field(ge=1, le=12)
    electricity_kwh: float = Field(default=0, ge=0)
    gas_m3: float = Field(default=0, ge=0)
    electricity_cost: float | None = None
    gas_cost: float | None = None


class EnergyBillCreate(EnergyBillBase):
    pass


class EnergyBillRead(EnergyBillBase):
    id: int
    building_id: int
    model_config = ConfigDict(from_attributes=True)


class WeatherDataCreate(BaseModel):
    city: str = "جاجرم"
    date: date
    temp_min: float | None = None
    temp_max: float | None = None
    temp_avg: float
    humidity: float | None = None
    solar_radiation: float | None = None
    rainfall: float | None = None
    wind_speed: float | None = None


class WeatherDataRead(WeatherDataCreate):
    id: int
    building_id: int
    model_config = ConfigDict(from_attributes=True)


class RecommendationRead(BaseModel):
    id: int
    building_id: int
    category: str
    recommendation: str
    impact_level: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class MonthlyEnergyRead(BaseModel):
    month: int
    electricity_kwh: float
    gas_m3: float
    electricity_mj: float
    gas_mj: float
    total_mj: float
    energy_per_m2: float
    energy_per_person: float


class WeatherMonthlyRead(BaseModel):
    month: int
    temp_avg: float
    humidity: float
    solar_radiation: float
    rainfall: float


class ElectricEquipmentBase(BaseModel):
    name: str
    category: str | None = None
    quantity: float = Field(default=1, ge=0)
    power_w: float = Field(default=0, ge=0)
    hours_per_day: float = Field(default=0, ge=0)
    days_per_year: float = Field(default=365, ge=0)
    usage_period: str | None = None


class ElectricEquipmentCreate(ElectricEquipmentBase):
    pass


class ElectricEquipmentRead(ElectricEquipmentBase):
    id: int | None = None
    building_id: int | None = None
    annual_kwh: float | None = None
    average_power_w: float | None = None
    model_config = ConfigDict(from_attributes=True)


class GasEquipmentBase(BaseModel):
    name: str
    category: str | None = None
    quantity: float = Field(default=1, ge=0)
    gas_m3_per_hour: float = Field(default=0, ge=0)
    hours_per_day: float = Field(default=0, ge=0)
    days_per_year: float = Field(default=365, ge=0)
    usage_period: str | None = None


class GasEquipmentCreate(GasEquipmentBase):
    pass


class GasEquipmentRead(GasEquipmentBase):
    id: int | None = None
    building_id: int | None = None
    annual_m3: float | None = None
    average_gas_m3_per_hour: float | None = None
    model_config = ConfigDict(from_attributes=True)


class AnomalyRead(BaseModel):
    month: int
    type: str
    message: str


class AuditResultRead(BaseModel):
    id: int
    building_id: int
    total_energy_mj: float
    eui: float
    energy_per_person: float
    hdd: float
    cdd: float
    energy_rating: str
    energy_index_ratio: float | None = None
    ideal_e2: float | None = None
    climate_zone: str | None = None
    standard_eui: float
    high_consumption_flag: bool
    created_at: datetime
    monthly: list[MonthlyEnergyRead] = []
    weather_monthly: list[WeatherMonthlyRead] = []
    electric_equipment: list[ElectricEquipmentRead] = []
    gas_equipment: list[GasEquipmentRead] = []
    energy_label_ranges: list[dict] = []
    anomalies: list[AnomalyRead] = []
    recommendations: list[RecommendationRead] = []
    model_config = ConfigDict(from_attributes=True)
