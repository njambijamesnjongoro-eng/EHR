import api from "../api";
import type {
  Patient,
  PatientFormData,
  PatientHistory,
  ApiResponse,
} from "../types";

export const patientApi = {
  async list(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    gender?: string;
    blood_group?: string;
    ordering?: string;
  }) {
    const response = await api.get<ApiResponse<Patient[]>>(
      "/api/patients/",
      { params }
    );
    return response.data;
  },

  async get(id: number | string) {
    const response = await api.get<ApiResponse<Patient>>(
      `/api/patients/${id}/`
    );
    return response.data;
  },

  async create(data: PatientFormData) {
    const response = await api.post<ApiResponse<Patient>>(
      "/api/patients/",
      data
    );
    return response.data;
  },

  async update(id: number | string, data: Partial<PatientFormData>) {
    const response = await api.patch<ApiResponse<Patient>>(
      `/api/patients/${id}/`,
      data
    );
    return response.data;
  },

  async deactivate(id: number | string) {
    const response = await api.delete<ApiResponse<null>>(
      `/api/patients/${id}/`
    );
    return response.data;
  },

  async quickSearch(query: string) {
    const response = await api.get<ApiResponse<Patient[]>>(
      "/api/patients/quick_search/",
      { params: { q: query } }
    );
    return response.data;
  },

  async getHistory(
    patientId: number | string,
    params?: { record_type?: string; page?: number }
  ) {
    const response = await api.get<ApiResponse<PatientHistory[]>>(
      `/api/patients/${patientId}/history/`,
      { params }
    );
    return response.data;
  },

  async addHistory(
    patientId: number | string,
    data: {
      record_type: string;
      title: string;
      description?: string;
      is_confidential?: boolean;
    }
  ) {
    const response = await api.post<ApiResponse<PatientHistory>>(
      `/api/patients/${patientId}/add_history/`,
      data
    );
    return response.data;
  },
};
