import api from "../api";
import type { ApiResponse, HospitalLoadAnalysis, ResourceAllocation, EfficiencyScore, OperationalAlert, DeviceTelemetryEvent, DeviceTelemetryAnalytics } from "../types";

export const operationsApi = {
  async hospitalLoad(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<HospitalLoadAnalysis>>("/api/analytics/efficiency/", { params });
    return res.data;
  },

  async resourceAllocation(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<ResourceAllocation>>("/api/analytics/resource-allocation/", { params });
    return res.data;
  },

  async bottlenecks(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>[]>>("/api/analytics/bottlenecks/", { params });
    return res.data;
  },

  async recommendations(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<string[]>>("/api/analytics/recommendations/", { params });
    return res.data;
  },

  async listAlerts(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<OperationalAlert[]>>("/api/security/operational-alerts/", { params });
    return res.data;
  },

  async threatIntel(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/security/threat-intel/", { params });
    return res.data;
  },

  async loginAnomalies(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>[]>>("/api/security/login-anomalies/", { params });
    return res.data;
  },

  async listMetrics(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>[]>>("/api/smart-hospital/metrics/", { params });
    return res.data;
  },

  async telemetrySummary(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/smart-hospital/telemetry-summary/", { params });
    return res.data;
  },

  async myTelemetry() {
    const res = await api.get<ApiResponse<DeviceTelemetryEvent[]>>("/api/citizen-portal/my-telemetry/");
    return res.data;
  },

  async populationInsights() {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/citizen-portal/population-insights/");
    return res.data;
  },
};
