import api from "../api";
import type { SystemHealthMetric, SystemHealthDashboard, EventStreamLog, ApiResponse } from "../types";

export const monitoringApi = {
  async listMetrics(params?: { metric_type?: string }) {
    const res = await api.get<ApiResponse<SystemHealthMetric[]>>("/api/monitoring/metrics/", { params });
    return res.data;
  },

  async getDashboard() {
    const res = await api.get<ApiResponse<SystemHealthDashboard>>("/api/monitoring/dashboard/");
    return res.data;
  },

  async getHealth() {
    const res = await api.get<{ status: string; checks: Record<string, unknown>; timestamp: string }>(
      "/api/monitoring/health/",
    );
    return res.data;
  },

  async getPrometheusMetrics() {
    const res = await api.get<{ metrics: string }>("/api/monitoring/prometheus/");
    return res.data;
  },

  async getInfrastructureHealth() {
    const res = await api.get<ApiResponse<{ overall_status: string; checks: Record<string, unknown> }>>(
      "/api/monitoring/infrastructure/health/",
    );
    return res.data;
  },

  async getOptimizationRecommendations() {
    const res = await api.get<ApiResponse<unknown[]>>("/api/monitoring/infrastructure/recommendations/");
    return res.data;
  },

  async runSelfHealing() {
    const res = await api.post<ApiResponse<{ actions_taken: string[] }>>("/api/monitoring/infrastructure/self-heal/");
    return res.data;
  },

  async listEventStream(params?: { event_source?: string; event_type?: string }) {
    const res = await api.get<ApiResponse<EventStreamLog[]>>("/api/monitoring/events/", { params });
    return res.data;
  },
};
