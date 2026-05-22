import api from "../api";
import type { AIRecommendation, ApiResponse } from "../types";

export const aiOrchestratorApi = {
  async list(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<AIRecommendation[]>>("/api/ai-orchestrator/recommendations/", { params });
    return res.data;
  },

  async detail(id: number) {
    const res = await api.get<ApiResponse<AIRecommendation>>(`/api/ai-orchestrator/recommendations/${id}/`);
    return res.data;
  },

  async accept(id: number) {
    const res = await api.post<ApiResponse<AIRecommendation>>(`/api/ai-orchestrator/recommendations/${id}/accept/`);
    return res.data;
  },

  async reject(id: number, reason?: string) {
    const res = await api.post<ApiResponse<AIRecommendation>>(`/api/ai-orchestrator/recommendations/${id}/reject/`, { rejection_reason: reason });
    return res.data;
  },

  async generateClinical(patient_id: number, visit_id?: number) {
    const res = await api.post<ApiResponse<AIRecommendation>>("/api/ai-orchestrator/generate-clinical/", { patient_id, visit_id });
    return res.data;
  },

  async generatePreventive(patient_id: number) {
    const res = await api.post<ApiResponse<AIRecommendation>>("/api/ai-orchestrator/generate-preventive/", { patient_id });
    return res.data;
  },

  async workflowOptimization(hospital_id?: number) {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/ai-orchestrator/workflow-optimization/", {
      params: { hospital_id },
    });
    return res.data;
  },
};
