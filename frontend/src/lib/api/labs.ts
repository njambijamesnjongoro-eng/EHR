import api from "../api";
import type {
  LabRequest,
  LabRequestFormData,
  LabResult,
  ApiResponse,
} from "../types";

export const labApi = {
  // ─── Lab Requests ───
  async listRequests(params?: {
    page?: number;
    patient?: number;
    status?: string;
    priority?: string;
    search?: string;
  }) {
    const response = await api.get<ApiResponse<LabRequest[]>>(
      "/api/labs/requests/",
      { params }
    );
    return response.data;
  },

  async createRequest(data: LabRequestFormData) {
    const response = await api.post<ApiResponse<LabRequest>>(
      "/api/labs/requests/",
      data
    );
    return response.data;
  },

  async updateRequestStatus(id: number, status: string) {
    const response = await api.patch<ApiResponse<LabRequest>>(
      `/api/labs/requests/${id}/`,
      { status }
    );
    return response.data;
  },

  async cancelRequest(id: number) {
    const response = await api.post<ApiResponse<null>>(
      `/api/labs/requests/${id}/cancel/`
    );
    return response.data;
  },

  // ─── Lab Results ───
  async listResults(params?: { patient?: number; lab_request?: number }) {
    const response = await api.get<ApiResponse<LabResult[]>>(
      "/api/labs/results/",
      { params }
    );
    return response.data;
  },

  async uploadResult(data: FormData) {
    const response = await api.post<ApiResponse<LabResult>>(
      "/api/labs/results/",
      data,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
    return response.data;
  },
};
