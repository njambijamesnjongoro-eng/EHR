import api from "../api";
import type { ImagingRequest, ImagingResult, ApiResponse } from "../types";

export const imagingApi = {
  async listRequests(params?: {
    page?: number; patient?: number; status?: string; imaging_type?: string;
  }) {
    const res = await api.get<ApiResponse<ImagingRequest[]>>("/api/imaging/requests/", { params });
    return res.data;
  },

  async createRequest(data: {
    visit: number; patient: number; imaging_type: string;
    priority: string; clinical_history?: string; region_examined?: string;
  }) {
    const res = await api.post<ApiResponse<ImagingRequest>>("/api/imaging/requests/", data);
    return res.data;
  },

  async listResults(params?: { patient?: number }) {
    const res = await api.get<ApiResponse<ImagingResult[]>>("/api/imaging/results/", { params });
    return res.data;
  },

  async uploadResult(data: FormData) {
    const res = await api.post<ApiResponse<ImagingResult>>("/api/imaging/results/", data, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },
};
