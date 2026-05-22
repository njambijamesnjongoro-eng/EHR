import api from "../api";
import type {
  SecurityEvent, DeviceFingerprint, RiskDashboard,
  MFAToken, ApiResponse,
} from "../types";

export const securityApi = {
  async listEvents(params?: { category?: string; severity?: string; resolved?: boolean }) {
    const res = await api.get<ApiResponse<SecurityEvent[]>>("/api/security/events/", { params });
    return res.data;
  },

  async getEvent(id: number) {
    const res = await api.get<ApiResponse<SecurityEvent>>(`/api/security/events/${id}/`);
    return res.data;
  },

  async resolveEvent(id: number) {
    const res = await api.post<ApiResponse<SecurityEvent>>(`/api/security/events/${id}/resolve/`);
    return res.data;
  },

  async listDevices(params?: { is_trusted?: boolean }) {
    const res = await api.get<ApiResponse<DeviceFingerprint[]>>("/api/security/devices/", { params });
    return res.data;
  },

  async trustDevice(id: number) {
    const res = await api.post<ApiResponse<DeviceFingerprint>>(`/api/security/devices/${id}/trust/`);
    return res.data;
  },

  async setupMfa(token_type = "totp") {
    const res = await api.post<ApiResponse<{ secret: string; token_type: string }>>("/api/security/mfa/setup/", { token_type });
    return res.data;
  },

  async verifyMfa(token_code: string) {
    const res = await api.post<ApiResponse<null>>("/api/security/mfa/verify/", { token_code });
    return res.data;
  },

  async disableMfa() {
    const res = await api.post<ApiResponse<null>>("/api/security/mfa/disable/");
    return res.data;
  },

  async getRiskDashboard() {
    const res = await api.get<ApiResponse<RiskDashboard>>("/api/security/risk-dashboard/");
    return res.data;
  },
};
