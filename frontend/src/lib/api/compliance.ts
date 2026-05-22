import api from "../api";
import type { ConsentLog, EnterpriseAuditEvent, AuditReport, ApiResponse } from "../types";

export const complianceApi = {
  async listConsents(params?: { consent_type?: string; status?: string; patient?: number }) {
    const res = await api.get<ApiResponse<ConsentLog[]>>("/api/compliance/consents/", { params });
    return res.data;
  },

  async getConsent(id: number) {
    const res = await api.get<ApiResponse<ConsentLog>>(`/api/compliance/consents/${id}/`);
    return res.data;
  },

  async grantConsent(data: { patient: number; consent_type: string; expires_days?: number; metadata?: Record<string, unknown> }) {
    const res = await api.post<ApiResponse<ConsentLog>>("/api/compliance/consents/grant/", data);
    return res.data;
  },

  async revokeConsent(id: number, reason?: string) {
    const res = await api.post<ApiResponse<ConsentLog>>(`/api/compliance/consents/${id}/revoke/`, { reason });
    return res.data;
  },

  async listAuditEvents(params?: { event_type?: string; severity?: string }) {
    const res = await api.get<ApiResponse<EnterpriseAuditEvent[]>>("/api/compliance/audit-events/", { params });
    return res.data;
  },

  async getAuditReport(days = 30) {
    const res = await api.get<ApiResponse<AuditReport>>("/api/compliance/audit-report/", { params: { days } });
    return res.data;
  },
};
