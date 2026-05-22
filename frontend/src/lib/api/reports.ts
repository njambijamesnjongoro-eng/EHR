import api from "../api";
import type { DashboardStats, ApiResponse } from "../types";

export const reportsApi = {
  async getDashboardStats() {
    const res = await api.get<ApiResponse<DashboardStats>>("/api/reports/dashboard/");
    return res.data;
  },

  async getRevenueReport(days = 30) {
    const res = await api.get<ApiResponse<unknown>>("/api/reports/revenue/", { params: { days } });
    return res.data;
  },

  async getClinicalReport(days = 30) {
    const res = await api.get<ApiResponse<unknown>>("/api/reports/clinical/", { params: { days } });
    return res.data;
  },
};
