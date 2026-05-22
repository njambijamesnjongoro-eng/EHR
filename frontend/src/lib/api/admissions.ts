import api from "../api";
import type { Ward, Bed, Admission, ApiResponse } from "../types";

export const admissionsApi = {
  async listWards() {
    const res = await api.get<ApiResponse<Ward[]>>("/api/admissions/wards/");
    return res.data;
  },

  async getWardBeds(wardId: number) {
    const res = await api.get<ApiResponse<Bed[]>>(`/api/admissions/wards/${wardId}/beds/`);
    return res.data;
  },

  async listBeds(params?: { ward?: number; occupancy_status?: string }) {
    const res = await api.get<ApiResponse<Bed[]>>("/api/admissions/beds/", { params });
    return res.data;
  },

  async listAdmissions(params?: {
    page?: number; status?: string; ward?: number; patient?: number; search?: string;
  }) {
    const res = await api.get<ApiResponse<Admission[]>>("/api/admissions/admissions/", { params });
    return res.data;
  },

  async admitPatient(data: {
    patient: number; ward: number; bed: number; admission_reason: string;
  }) {
    const res = await api.post<ApiResponse<Admission>>("/api/admissions/admissions/", data);
    return res.data;
  },

  async dischargePatient(id: number, discharge_notes: string) {
    const res = await api.post<ApiResponse<null>>(`/api/admissions/admissions/${id}/discharge/`, { discharge_notes });
    return res.data;
  },

  async transferPatient(id: number, ward: number, bed: number) {
    const res = await api.post<ApiResponse<null>>(`/api/admissions/admissions/${id}/transfer/`, { ward, bed });
    return res.data;
  },
};
