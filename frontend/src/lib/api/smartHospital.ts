import api from "../api";
import type { SmartHospitalDevice, ApiResponse } from "../types";

export const smartHospitalApi = {
  async listDevices(params?: { hospital?: number; device_category?: string; is_online?: boolean }) {
    const res = await api.get<ApiResponse<SmartHospitalDevice[]>>("/api/smart-hospital/devices/", { params });
    return res.data;
  },

  async getDevice(id: number) {
    const res = await api.get<ApiResponse<SmartHospitalDevice>>(`/api/smart-hospital/devices/${id}/`);
    return res.data;
  },

  async registerDevice(data: {
    device_category: string; device_name: string; serial_number: string;
    ward_id?: number; ip_address?: string; mac_address?: string;
  }) {
    const res = await api.post<ApiResponse<SmartHospitalDevice>>("/api/smart-hospital/devices/register/", data);
    return res.data;
  },

  async getBedOccupancy(hospital_id: number) {
    const res = await api.get<ApiResponse<{ wards: unknown[]; overall_utilization_pct: number }>>(
      `/api/smart-hospital/hospitals/${hospital_id}/bed-occupancy/`,
    );
    return res.data;
  },

  async getOfflineDevices(hospital_id?: number, minutes = 15) {
    const res = await api.get<ApiResponse<{ offline_count: number; devices: SmartHospitalDevice[] }>>(
      "/api/smart-hospital/devices/offline/", { params: { hospital_id, minutes } },
    );
    return res.data;
  },
};
