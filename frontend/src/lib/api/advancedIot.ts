import api from "../api";
import type { ApiResponse } from "../types";

export const advancedIotApi = {
  async patientWearableSummary(patient_id: number) {
    const res = await api.get<ApiResponse<{ patient_id: number; active_devices: number; readings_24h: number; abnormal_readings: number; last_reading: string | null }>>(
      `/api/smart-hospital/devices/${patient_id}/health/`
    );
    return res.data;
  },

  async detectEmergency(patient_id: number) {
    const res = await api.post<ApiResponse<{ emergency: boolean }>>("/api/smart-hospital/detect-emergency/", { patient_id });
    return res.data;
  },
};
