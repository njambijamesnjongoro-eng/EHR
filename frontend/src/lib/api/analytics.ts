import api from "../api";
import type { HospitalDashboardData, RevenueMonthly, NationalAggregate, HospitalLoadPrediction, PredictiveAlert, ApiResponse } from "../types";

export const analyticsApi = {
  async getDashboard(days = 30) {
    const res = await api.get<ApiResponse<HospitalDashboardData>>("/api/analytics/dashboard/", { params: { days } });
    return res.data;
  },

  async getRevenue(months = 12) {
    const res = await api.get<ApiResponse<{ monthly: RevenueMonthly[]; total_revenue: number; total_collected: number }>>(
      "/api/analytics/revenue/", { params: { months } },
    );
    return res.data;
  },

  async getDiseaseTrends(days = 365) {
    const res = await api.get<ApiResponse<unknown[]>>("/api/analytics/disease-trends/", { params: { days } });
    return res.data;
  },

  async getDepartmentUtilization() {
    const res = await api.get<ApiResponse<unknown[]>>("/api/analytics/departments/");
    return res.data;
  },

  async getNationalAggregate() {
    const res = await api.get<ApiResponse<NationalAggregate>>("/api/analytics/national/");
    return res.data;
  },

  async getPredictiveHospitalLoad(days_ahead = 7) {
    const res = await api.get<ApiResponse<HospitalLoadPrediction>>(
      "/api/analytics/predictive/hospital-load/", { params: { days_ahead } },
    );
    return res.data;
  },

  async getPredictivePatientFlow(days_ahead = 30) {
    const res = await api.get<ApiResponse<unknown>>(
      "/api/analytics/predictive/patient-flow/", { params: { days_ahead } },
    );
    return res.data;
  },

  async getPredictiveAlerts(category?: string) {
    const res = await api.get<ApiResponse<PredictiveAlert[]>>(
      "/api/analytics/predictive/alerts/", { params: { category } },
    );
    return res.data;
  },

  async getSystemAnomalies() {
    const res = await api.get<ApiResponse<unknown[]>>("/api/analytics/predictive/anomalies/");
    return res.data;
  },
};
