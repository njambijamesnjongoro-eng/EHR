import api from "../api";
import type { CitizenHealthProfile, ApiResponse } from "../types";

export const citizenPortalApi = {
  async getHealthSummary() {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/citizen-portal/health-summary/");
    return res.data;
  },

  async getProfile() {
    const res = await api.get<ApiResponse<CitizenHealthProfile>>("/api/citizen-portal/profile/");
    return res.data;
  },

  async updateProfile(data: Partial<CitizenHealthProfile>) {
    const res = await api.patch<ApiResponse<CitizenHealthProfile>>("/api/citizen-portal/profile/", data);
    return res.data;
  },

  async getAppointments() {
    const res = await api.get<ApiResponse<unknown[]>>("/api/citizen-portal/appointments/");
    return res.data;
  },

  async getPrescriptions() {
    const res = await api.get<ApiResponse<unknown[]>>("/api/citizen-portal/prescriptions/");
    return res.data;
  },

  async getWearableDevices() {
    const res = await api.get<ApiResponse<unknown[]>>("/api/citizen-portal/wearable-devices/");
    return res.data;
  },

  async getReadings() {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/citizen-portal/readings/");
    return res.data;
  },
};
