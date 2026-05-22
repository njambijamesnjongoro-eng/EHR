import api from "../api";
import type { Notification, ApiResponse } from "../types";

export const notificationsApi = {
  async list() {
    const res = await api.get<ApiResponse<Notification[]>>("/api/notifications/");
    return res.data;
  },

  async unreadCount() {
    const res = await api.get<ApiResponse<{ count: number }>>("/api/notifications/unread_count/");
    return res.data;
  },

  async markRead(id: number) {
    const res = await api.post<ApiResponse<null>>(`/api/notifications/${id}/mark_read/`);
    return res.data;
  },

  async markAllRead() {
    const res = await api.post<ApiResponse<null>>("/api/notifications/mark_all_read/");
    return res.data;
  },
};
