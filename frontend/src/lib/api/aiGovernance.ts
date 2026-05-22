import api from "../api";
import type { ApiResponse, AIModelRegistry, ModelGovernanceReport } from "../types";

export const aiGovernanceApi = {
  async listModels(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<AIModelRegistry[]>>("/api/ai-governance/models/", { params });
    return res.data;
  },

  async modelDetail(id: number) {
    const res = await api.get<ApiResponse<AIModelRegistry>>(`/api/ai-governance/models/${id}/`);
    return res.data;
  },

  async updateStatus(id: number, status: string) {
    const res = await api.post<ApiResponse<AIModelRegistry>>(`/api/ai-governance/models/${id}/status/`, { status });
    return res.data;
  },

  async governanceReport(id: number) {
    const res = await api.get<ApiResponse<ModelGovernanceReport>>(`/api/ai-governance/models/${id}/governance/`);
    return res.data;
  },

  async auditTrail(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>[]>>("/api/ai-governance/audit-trail/", { params });
    return res.data;
  },
};
