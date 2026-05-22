import api from "../api";
import type { SyncStatus, SyncQueueItem, ApiResponse } from "../types";

export const syncApi = {
  async getStatus() {
    const res = await api.get<ApiResponse<SyncStatus>>("/api/sync/status/");
    return res.data;
  },

  async getPending() {
    const res = await api.get<ApiResponse<SyncQueueItem[]>>("/api/sync/pending/");
    return res.data;
  },

  async getLogs() {
    const res = await api.get<ApiResponse<unknown[]>>("/api/sync/logs/");
    return res.data;
  },

  async push(items: Partial<SyncQueueItem>[]) {
    const res = await api.post<ApiResponse<{ processed: number; failed: number }>>("/api/sync/push/", { items });
    return res.data;
  },
};
