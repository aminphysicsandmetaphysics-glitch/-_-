import { AuditResult, Building } from "../types/audit";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export const api = {
  listBuildings: () => request<Building[]>("/buildings"),
  createBuilding: (payload: Omit<Building, "id">) =>
    request<Building>("/buildings", { method: "POST", body: JSON.stringify(payload) }),
  saveBills: (buildingId: number, payload: unknown[]) =>
    request(`/buildings/${buildingId}/bills`, { method: "POST", body: JSON.stringify(payload) }),
  saveWeather: (buildingId: number, payload: unknown[]) =>
    request(`/buildings/${buildingId}/weather`, { method: "POST", body: JSON.stringify(payload) }),
  runAudit: (buildingId: number) =>
    request<AuditResult>(`/buildings/${buildingId}/audit/run`, { method: "POST" }),
  latestAudit: (buildingId: number) => request<AuditResult>(`/buildings/${buildingId}/audit/latest`),
  pdfUrl: (buildingId: number) => `${API_BASE}/buildings/${buildingId}/reports/pdf`,
  excelUrl: (buildingId: number) => `${API_BASE}/buildings/${buildingId}/reports/excel`,
};
