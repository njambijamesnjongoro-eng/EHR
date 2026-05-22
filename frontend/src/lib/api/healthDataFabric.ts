import api from "../api";
import type { ApiResponse, InfrastructureEvent, EventChainItem, CorrelatedEvents } from "../types";

export const healthDataFabricApi = {
  async listEvents(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>[]>>("/api/data-fabric/events/", { params });
    return res.data;
  },

  async emitEvent(data: Record<string, unknown>) {
    const res = await api.post<ApiResponse<Record<string, unknown>>>("/api/data-fabric/events/emit/", data);
    return res.data;
  },

  async eventChain(correlation_id: string) {
    const res = await api.get<ApiResponse<EventChainItem[]>>("/api/data-fabric/events/chain/", {
      params: { correlation_id },
    });
    return res.data;
  },

  async correlateEvents(aggregate_type: string, aggregate_id: string) {
    const res = await api.get<ApiResponse<CorrelatedEvents>>("/api/data-fabric/events/correlate/", {
      params: { aggregate_type, aggregate_id },
    });
    return res.data;
  },

  async eventMetrics(hours?: number) {
    const res = await api.get<ApiResponse<Record<string, number>>>("/api/data-fabric/events/metrics/", {
      params: { hours },
    });
    return res.data;
  },

  async listInfrastructure(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<InfrastructureEvent[]>>("/api/data-fabric/infrastructure/", { params });
    return res.data;
  },

  async infrastructureDetail(id: number) {
    const res = await api.get<ApiResponse<InfrastructureEvent>>(`/api/data-fabric/infrastructure/${id}/`);
    return res.data;
  },

  async logInfrastructure(data: Record<string, unknown>) {
    const res = await api.post<ApiResponse<InfrastructureEvent>>("/api/data-fabric/infrastructure/log/", data);
    return res.data;
  },

  async recentErrors(hours?: number) {
    const res = await api.get<ApiResponse<InfrastructureEvent[]>>("/api/data-fabric/infrastructure/errors/", {
      params: { hours },
    });
    return res.data;
  },

  async recordPrediction(data: Record<string, unknown>) {
    const res = await api.post<ApiResponse<Record<string, unknown>>>("/api/data-fabric/predictions/record/", data);
    return res.data;
  },
};
