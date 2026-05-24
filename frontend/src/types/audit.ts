export type Building = {
  id: number;
  project_name: string;
  city: string;
  address?: string;
  area_m2: number;
  floors?: number;
  year_built?: number;
  occupants: number;
  building_type: string;
  heating_system?: string;
  cooling_system?: string;
  lighting_type?: string;
  window_type?: string;
  wall_type?: string;
  roof_type?: string;
  climate_zone?: string;
  ideal_e2?: number | null;
  has_insulation: boolean;
  has_thermostat: boolean;
  has_shading: boolean;
  orientation?: string;
};

export type MonthlyEnergy = {
  month: number;
  electricity_kwh: number;
  gas_m3: number;
  electricity_mj: number;
  gas_mj: number;
  total_mj: number;
  energy_per_m2: number;
  energy_per_person: number;
};

export type Recommendation = {
  id: number;
  category: string;
  recommendation: string;
  impact_level: string;
  status: string;
};

export type WeatherMonthly = {
  month: number;
  temp_avg: number;
  humidity: number;
  solar_radiation: number;
  rainfall: number;
};

export type ElectricEquipment = {
  id?: number;
  building_id?: number;
  name: string;
  category?: string;
  quantity: number;
  power_w: number;
  hours_per_day: number;
  days_per_year: number;
  usage_period?: string;
  annual_kwh?: number;
  average_power_w?: number;
};

export type GasEquipment = {
  id?: number;
  building_id?: number;
  name: string;
  category?: string;
  quantity: number;
  gas_m3_per_hour: number;
  hours_per_day: number;
  days_per_year: number;
  usage_period?: string;
  annual_m3?: number;
  average_gas_m3_per_hour?: number;
};

export type Anomaly = {
  month: number;
  type: string;
  message: string;
};

export type AuditResult = {
  id: number;
  building_id: number;
  total_energy_mj: number;
  eui: number;
  energy_per_person: number;
  hdd: number;
  cdd: number;
  energy_rating: string;
  energy_index_ratio?: number;
  ideal_e2?: number;
  climate_zone?: string;
  standard_eui: number;
  high_consumption_flag: boolean;
  monthly: MonthlyEnergy[];
  weather_monthly: WeatherMonthly[];
  electric_equipment: ElectricEquipment[];
  gas_equipment: GasEquipment[];
  energy_label_ranges: Array<Record<string, string | number>>;
  anomalies: Anomaly[];
  recommendations: Recommendation[];
};
