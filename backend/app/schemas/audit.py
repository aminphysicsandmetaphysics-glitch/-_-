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


class AuditResultRead(BaseModel):
    id: int
    building_id: int
    total_energy_mj: float
    eui: float
    energy_per_person: float
    hdd: float
    cdd: float
    energy_rating: str
    standard_eui: float
    high_consumption_flag: bool
    created_at: datetime
    monthly: list[MonthlyEnergyRead] = []
    recommendations: list[RecommendationRead] = []
    model_config = ConfigDict(from_attributes=True)
