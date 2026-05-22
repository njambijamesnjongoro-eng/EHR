import api from "../api";
import type { Hospital, Department, HospitalStaff, ApiResponse } from "../types";

export const hospitalApi = {
  async list(params?: { county?: string; hospital_type?: string; search?: string }) {
    const res = await api.get<ApiResponse<Hospital[]>>("/api/hospitals/hospitals/", { params });
    return res.data;
  },

  async get(id: number) {
    const res = await api.get<ApiResponse<Hospital>>(`/api/hospitals/hospitals/${id}/`);
    return res.data;
  },

  async create(data: Partial<Hospital>) {
    const res = await api.post<ApiResponse<Hospital>>("/api/hospitals/hospitals/", data);
    return res.data;
  },

  async update(id: number, data: Partial<Hospital>) {
    const res = await api.patch<ApiResponse<Hospital>>(`/api/hospitals/hospitals/${id}/`, data);
    return res.data;
  },

  async listDepartments(hospitalId: number) {
    const res = await api.get<ApiResponse<Department[]>>(`/api/hospitals/hospitals/${hospitalId}/departments/`);
    return res.data;
  },

  async listStaff(hospitalId: number) {
    const res = await api.get<ApiResponse<HospitalStaff[]>>(`/api/hospitals/hospitals/${hospitalId}/staff/`);
    return res.data;
  },

  async createDepartment(data: Partial<Department>) {
    const res = await api.post<ApiResponse<Department>>("/api/hospitals/departments/", data);
    return res.data;
  },

  async createStaff(data: Partial<HospitalStaff>) {
    const res = await api.post<ApiResponse<HospitalStaff>>("/api/hospitals/staff/", data);
    return res.data;
  },
};
