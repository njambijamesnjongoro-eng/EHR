import api from "../api";
import type { PublicHealthMetric, OutbreakSignal, ApiResponse } from "../types";

export const publicHealthApi = {
  async listMetrics(params?: { metric_category?: string; county?: string }) {
    const res = await api.get<ApiResponse<PublicHealthMetric[]>>("/api/public-health/metrics/", { params });
    return res.data;
  },

  async getDiseasePrevalence(days = 90) {
    const res = await api.get<ApiResponse<{ period_days: number; diseases: unknown[] }>>(
      "/api/public-health/disease-prevalence/", { params: { days } },
    );
    return res.data;
  },

  async getOutbreakSignals(days = 14) {
    const res = await api.get<ApiResponse<OutbreakSignal[]>>("/api/public-health/outbreak-signals/", { params: { days } });
    return res.data;
  },

  async getCountyHeatmap(disease_code?: string, days = 30) {
    const res = await api.get<ApiResponse<{ counties: unknown[] }>>("/api/public-health/county-heatmap/", {
      params: { disease_code, days },
    });
    return res.data;
  },

  async getHealthcareBurden(days = 30) {
    const res = await api.get<ApiResponse<unknown>>("/api/public-health/healthcare-burden/", { params: { days } });
    return res.data;
  },

  async getVaccinationAnalytics() {
    const res = await api.get<ApiResponse<unknown>>("/api/public-health/vaccination-analytics/");
    return res.data;
  },

  async getMortalityTrends(days = 365) {
    const res = await api.get<ApiResponse<unknown>>("/api/public-health/mortality-trends/", { params: { days } });
    return res.data;
  },
};
