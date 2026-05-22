import api from "../api";
import type { ApiResponse, CitizenFullHealthRecord, EmergencyProfile, HealthShareResult, CareReminder } from "../types";

export const citizenSuperPortalApi = {
  async fullHealthRecord() {
    const res = await api.get<ApiResponse<CitizenFullHealthRecord>>("/api/citizen-portal/full-health-record/");
    return res.data;
  },

  async emergencyProfile() {
    const res = await api.get<ApiResponse<EmergencyProfile>>("/api/citizen-portal/emergency-profile/");
    return res.data;
  },

  async shareData(recipient_email: string, data_types: string[], expiry_hours?: number) {
    const res = await api.post<ApiResponse<HealthShareResult>>("/api/citizen-portal/share-data/", {
      recipient_email, data_types, expiry_hours,
    });
    return res.data;
  },

  async careReminders() {
    const res = await api.get<ApiResponse<CareReminder[]>>("/api/citizen-portal/care-reminders/");
    return res.data;
  },
};
