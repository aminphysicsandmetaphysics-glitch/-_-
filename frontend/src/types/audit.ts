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

export type AuditResult = {
  id: number;
  building_id: number;
  total_energy_mj: number;
  eui: number;
  energy_per_person: number;
  hdd: number;
  cdd: number;
  energy_rating: string;
  standard_eui: number;
  high_consumption_flag: boolean;
  monthly: MonthlyEnergy[];
  recommendations: Recommendation[];
};
