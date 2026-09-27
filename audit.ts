export type User = {
  id: number;
  email: string;
  full_name?: string | null;
  created_at: string;
};

export type Building = {
  id: number;
  owner_id?: number | null;
  project_name: string;
  city: string;
  address?: string;
  latitude?: number | null;
  longitude?: number | null;
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
  wall_area_m2?: number | null;
  roof_area_m2?: number | null;
  floor_area_m2?: number | null;
  window_area_m2?: number | null;
  wall_material_key?: string | null;
  roof_material_key?: string | null;
  floor_material_key?: string | null;
  window_material_key?: string | null;
  airtightness?: string | null;
};

export type EnvelopeMaterial = {
  key: string;
  category: "wall" | "roof" | "floor" | "window";
  label_fa: string;
  label_en: string;
  u_value: number;
  insulated: boolean;
  notes_fa?: string;
};

export type EquipmentPreset = {
  key: string;
  fuel: "electric" | "gas";
  category: string;
  label_fa: string;
  label_en: string;
  typical_power_w: number;
  typical_gas_m3_per_hour: number;
  typical_hours_per_day: number;
  typical_days_per_year: number;
  efficiency_note_fa?: string;
};

export type WeatherRow = {
  date: string;
  temp_min?: number;
  temp_max?: number;
  temp_avg: number;
  humidity?: number;
  solar_radiation?: number;
  rainfall?: number;
  wind_speed?: number;
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
  quantified: boolean;
  estimated_annual_savings_mj?: number | null;
  estimated_annual_savings_toman?: number | null;
  estimated_annual_co2_avoided_kg?: number | null;
  estimated_cost_toman_low?: number | null;
  estimated_cost_toman_high?: number | null;
  estimated_payback_years_low?: number | null;
  estimated_payback_years_high?: number | null;
  savings_base_source?: string | null;
  precision?: string;
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

export type EnvelopeBreakdown = {
  geometry: Record<string, number | Record<string, boolean>>;
  u_values: Record<string, number>;
  ach: number;
  h_wall_w_k: number;
  h_roof_w_k: number;
  h_floor_w_k: number;
  h_window_w_k: number;
  h_transmission_w_k: number;
  h_infiltration_w_k: number;
  h_total_w_k: number;
};

export type CarbonFootprint = {
  electricity_co2_kg: number;
  gas_co2_kg: number;
  total_co2_kg: number;
  total_co2_tonnes: number;
};

export type Confidence = {
  confidence_score: number;
  confidence_level: "low" | "medium" | "high";
  bill_months_used: number;
  weather_days_used: number;
  regression_r_squared: number | null;
};

export type EnergySignature = {
  baseload_mj_per_month: number;
  heating_signature_mj_per_hdd: number;
  cooling_signature_mj_per_cdd: number;
  r_squared: number;
  implied_annual_heating_mj: number;
  implied_annual_cooling_mj: number;
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
  theoretical_heating_mj?: number | null;
  theoretical_cooling_mj?: number | null;
  envelope_diagnosis?: string | null;
  total_co2_kg?: number | null;
  performance_score?: number | null;
  monthly: MonthlyEnergy[];
  weather_monthly: WeatherMonthly[];
  electric_equipment: ElectricEquipment[];
  gas_equipment: GasEquipment[];
  energy_label_ranges: Array<Record<string, string | number>>;
  anomalies: Anomaly[];
  recommendations: Recommendation[];
  envelope_breakdown?: EnvelopeBreakdown | null;
  carbon_footprint?: CarbonFootprint | null;
  confidence?: Confidence | null;
  energy_signature?: EnergySignature | null;
};
