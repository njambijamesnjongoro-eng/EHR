import api from "../api";
import type { ExternalSystem, ApiResponse } from "../types";

export const interopApi = {
  async listSystems(params?: { system_type?: string; is_active?: boolean }) {
    const res = await api.get<ApiResponse<ExternalSystem[]>>("/api/interop/systems/", { params });
    return res.data;
  },

  async getSystem(id: number) {
    const res = await api.get<ApiResponse<ExternalSystem>>(`/api/interop/systems/${id}/`);
    return res.data;
  },

  async registerSystem(data: { system_name: string; system_type: string; base_url: string; auth_type?: string; config?: Record<string, unknown> }) {
    const res = await api.post<ApiResponse<ExternalSystem>>("/api/interop/systems/register/", data);
    return res.data;
  },

  async convertToFhir(resource_type: string, data: Record<string, unknown>) {
    const res = await api.post<ApiResponse<Record<string, unknown>>>("/api/interop/fhir/convert/", { resource_type, data });
    return res.data;
  },

  async importFromFhir(fhirResource: Record<string, unknown>) {
    const res = await api.post<ApiResponse<Record<string, unknown>>>("/api/interop/fhir/import/", fhirResource);
    return res.data;
  },
};
