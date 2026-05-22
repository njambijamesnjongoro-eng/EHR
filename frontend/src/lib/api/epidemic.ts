import api from "../api";
import type { ApiResponse, EpidemicAlert, RegionalSpread, PublicHealthForecast } from "../types";

export const epidemicApi = {
  async listAlerts(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<EpidemicAlert[]>>("/api/epidemic/alerts/", { params });
    return res.data;
  },

  async alertDetail(id: number) {
    const res = await api.get<ApiResponse<EpidemicAlert>>(`/api/epidemic/alerts/${id}/`);
    return res.data;
  },

  async resolveAlert(id: number) {
    const res = await api.post<ApiResponse<EpidemicAlert>>(`/api/epidemic/alerts/${id}/resolve/`);
    return res.data;
  },

  async detectOutbreak(days?: number) {
    const res = await api.post<ApiResponse<EpidemicAlert[]>>("/api/epidemic/detect-outbreak/", { days });
    return res.data;
  },

  async regionalSpread(disease_code: string, days?: number) {
    const res = await api.get<ApiResponse<RegionalSpread>>("/api/epidemic/regional-spread/", {
      params: { disease_code, days },
    });
    return res.data;
  },

  async forecast(disease_code: string, county?: string, days_ahead?: number) {
    const res = await api.post<ApiResponse<PublicHealthForecast>>("/api/epidemic/forecast/", {
      disease_code, county, days_ahead,
    });
    return res.data;
  },
};
