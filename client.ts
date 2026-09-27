import { AuditResult, Building, ElectricEquipment, EnvelopeMaterial, EquipmentPreset, GasEquipment, User, WeatherRow } from "../types/audit";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api/v1";

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json", ...(init?.headers as Record<string, string> ?? {}) };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  // --- auth ---
  register: (email: string, password: string, full_name: string) =>
    request<User>("/auth/register", { method: "POST", body: JSON.stringify({ email, password, full_name }) }),
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request<User>("/auth/me"),

  // --- catalogs ---
  envelopeCatalog: (category?: string) => request<EnvelopeMaterial[]>(`/catalogs/envelope${category ? `?category=${category}` : ""}`),
  equipmentCatalog: (fuel?: string) => request<EquipmentPreset[]>(`/catalogs/equipment${fuel ? `?fuel=${fuel}` : ""}`),

  // --- buildings ---
  listBuildings: () => request<Building[]>("/buildings"),
  createBuilding: (payload: Partial<Building>) => request<Building>("/buildings", { method: "POST", body: JSON.stringify(payload) }),
  getBuilding: (buildingId: number) => request<Building>(`/buildings/${buildingId}`),

  saveBills: (buildingId: number, payload: unknown[]) =>
    request(`/buildings/${buildingId}/bills`, { method: "POST", body: JSON.stringify(payload) }),
  listBills: (buildingId: number) => request<unknown[]>(`/buildings/${buildingId}/bills`),

  saveWeather: (buildingId: number, payload: unknown[]) =>
    request<WeatherRow[]>(`/buildings/${buildingId}/weather`, { method: "POST", body: JSON.stringify(payload) }),
  listWeather: (buildingId: number) => request<WeatherRow[]>(`/buildings/${buildingId}/weather`),
  autoFetchWeather: (buildingId: number, city?: string) =>
    request<WeatherRow[]>(`/buildings/${buildingId}/weather/auto-fetch`, { method: "POST", body: JSON.stringify({ city }) }),
  importWeatherExcel: (buildingId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const headers: Record<string, string> = {};
    if (authToken) headers.Authorization = `Bearer ${authToken}`;
    return fetch(`${API_BASE}/buildings/${buildingId}/weather/import`, { method: "POST", body: form, headers }).then((r) => {
      if (!r.ok) throw new Error("Import failed");
      return r.json();
    });
  },

  saveElectricEquipment: (buildingId: number, payload: unknown[]) =>
    request<ElectricEquipment[]>(`/buildings/${buildingId}/equipment/electric`, { method: "POST", body: JSON.stringify(payload) }),
  saveGasEquipment: (buildingId: number, payload: unknown[]) =>
    request<GasEquipment[]>(`/buildings/${buildingId}/equipment/gas`, { method: "POST", body: JSON.stringify(payload) }),

  runAudit: (buildingId: number) => request<AuditResult>(`/buildings/${buildingId}/audit/run`, { method: "POST" }),
  latestAudit: (buildingId: number) => request<AuditResult>(`/buildings/${buildingId}/audit/latest`),

  pdfUrl: (buildingId: number) => `${API_BASE}/buildings/${buildingId}/reports/pdf`,
  excelUrl: (buildingId: number) => `${API_BASE}/buildings/${buildingId}/reports/excel`,

  async downloadReport(url: string, filename: string) {
    const headers: Record<string, string> = {};
    if (authToken) headers.Authorization = `Bearer ${authToken}`;
    const response = await fetch(url, { headers });
    if (!response.ok) throw new Error("Report download failed");
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(objectUrl);
  },
};
