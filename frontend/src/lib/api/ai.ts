import api from "../api";
import type { AIInsight, ApiResponse } from "../types";

export const aiApi = {
  async listInsights(params?: { insight_type?: string; patient?: number; is_reviewed?: boolean }) {
    const res = await api.get<ApiResponse<AIInsight[]>>("/api/ai/insights/", { params });
    return res.data;
  },

  async getInsight(id: number) {
    const res = await api.get<ApiResponse<AIInsight>>(`/api/ai/insights/${id}/`);
    return res.data;
  },

  async reviewInsight(id: number, action_taken?: string) {
    const res = await api.post<ApiResponse<AIInsight>>(`/api/ai/insights/${id}/review/`, { action_taken });
    return res.data;
  },

  async assessRisk(patient_id: number) {
    const res = await api.post<ApiResponse<AIInsight>>("/api/ai/assess-risk/", { patient_id });
    return res.data;
  },

  async checkMedications(patient_id: number) {
    const res = await api.post<ApiResponse<AIInsight>>("/api/ai/check-medications/", { patient_id });
    return res.data;
  },

  async detectDeterioration(patient_id: number) {
    const res = await api.post<ApiResponse<AIInsight>>("/api/ai/detect-deterioration/", { patient_id });
    return res.data;
  },
};
