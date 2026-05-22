import api from "../api";
import type { ApiResponse, InfrastructureTwin, TwinSimulationResult } from "../types";

export const digitalTwinApi = {
  async list(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<InfrastructureTwin[]>>("/api/digital-twin/twins/", { params });
    return res.data;
  },

  async detail(id: number) {
    const res = await api.get<ApiResponse<InfrastructureTwin>>(`/api/digital-twin/twins/${id}/`);
    return res.data;
  },

  async runSimulation(id: number) {
    const res = await api.post<ApiResponse<TwinSimulationResult>>(`/api/digital-twin/twins/${id}/simulate/`);
    return res.data;
  },

  async status(id: number) {
    const res = await api.get<ApiResponse<InfrastructureTwin>>(`/api/digital-twin/twins/${id}/status/`);
    return res.data;
  },

  async createScenario(id: number, params: Record<string, unknown>) {
    const res = await api.post<ApiResponse<Record<string, unknown>>>(`/api/digital-twin/twins/${id}/scenarios/`, params);
    return res.data;
  },

  async compareScenarios(id: number) {
    const res = await api.get<ApiResponse<Record<string, unknown>>>(`/api/digital-twin/twins/${id}/compare/`);
    return res.data;
  },
};
