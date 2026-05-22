import api from "../api";
import type { ApiResponse, PopulationHealthInsight, PredictiveForecast, PopulationTrend } from "../types";

export const populationHealthApi = {
  async listInsights(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<PopulationHealthInsight[]>>("/api/population-health/insights/", { params });
    return res.data;
  },

  async recordInsight(data: Record<string, unknown>) {
    const res = await api.post<ApiResponse<PopulationHealthInsight>>("/api/population-health/insights/record/", data);
    return res.data;
  },

  async diseaseBurden(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/population-health/disease-burden/", { params });
    return res.data;
  },

  async healthcareAccess(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/population-health/healthcare-access/", { params });
    return res.data;
  },

  async healthEquity() {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/population-health/health-equity/");
    return res.data;
  },

  async regionalComparison(regions: string) {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/population-health/regional-comparison/", { params: { regions } });
    return res.data;
  },

  async listForecasts(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<PredictiveForecast[]>>("/api/population-health/forecasts/", { params });
    return res.data;
  },

  async recordForecast(data: Record<string, unknown>) {
    const res = await api.post<ApiResponse<PredictiveForecast>>("/api/population-health/forecasts/record/", data);
    return res.data;
  },
};
