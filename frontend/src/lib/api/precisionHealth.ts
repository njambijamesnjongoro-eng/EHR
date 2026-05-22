import api from "../api";
import type { ApiResponse, HealthRiskProfile, PatientRiskSummary } from "../types";

export const precisionHealthApi = {
  async listProfiles(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<HealthRiskProfile[]>>("/api/precision-health/profiles/", { params });
    return res.data;
  },

  async profileDetail(id: number) {
    const res = await api.get<ApiResponse<HealthRiskProfile>>(`/api/precision-health/profiles/${id}/`);
    return res.data;
  },

  async assessRisk(patient_id: number, risk_category: string) {
    const res = await api.post<ApiResponse<HealthRiskProfile>>("/api/precision-health/assess-risk/", { patient_id, risk_category });
    return res.data;
  },

  async patientRiskSummary(patient_id: number) {
    const res = await api.get<ApiResponse<PatientRiskSummary>>(`/api/precision-health/patients/${patient_id}/risk-summary/`);
    return res.data;
  },

  async highRisk(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<HealthRiskProfile[]>>("/api/precision-health/high-risk/", { params });
    return res.data;
  },

  async riskTrends(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/precision-health/risk-trends/", { params });
    return res.data;
  },
};
