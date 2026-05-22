import api from "../api";
import type { ApiResponse, EmergencyResponseEvent, NationalEmergencyOverview, RegionalCapacity } from "../types";

export const emergencyResponseApi = {
  async list(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<EmergencyResponseEvent[]>>("/api/emergency/events/", { params });
    return res.data;
  },

  async detail(id: number) {
    const res = await api.get<ApiResponse<EmergencyResponseEvent>>(`/api/emergency/events/${id}/`);
    return res.data;
  },

  async updateStatus(id: number, status: string) {
    const res = await api.post<ApiResponse<EmergencyResponseEvent>>(`/api/emergency/events/${id}/status/`, { status });
    return res.data;
  },

  async activeEmergencies() {
    const res = await api.get<ApiResponse<EmergencyResponseEvent[]>>("/api/emergency/active/");
    return res.data;
  },

  async regionalCapacity(region: string) {
    const res = await api.get<ApiResponse<RegionalCapacity>>("/api/emergency/regional-capacity/", { params: { region } });
    return res.data;
  },

  async nationalOverview() {
    const res = await api.get<ApiResponse<NationalEmergencyOverview>>("/api/emergency/national-overview/");
    return res.data;
  },
};
