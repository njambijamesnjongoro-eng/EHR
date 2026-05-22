import api from "../api";
import type { WearableDevice, DeviceReading, ApiResponse } from "../types";

export const wearableApi = {
  async listDevices(params?: { patient?: number; device_type?: string }) {
    const res = await api.get<ApiResponse<WearableDevice[]>>("/api/wearable/devices/", { params });
    return res.data;
  },

  async getDevice(id: number) {
    const res = await api.get<ApiResponse<WearableDevice>>(`/api/wearable/devices/${id}/`);
    return res.data;
  },

  async registerDevice(data: {
    patient: number; device_type: string; device_name: string;
    manufacturer?: string; serial_number: string; firmware_version?: string;
  }) {
    const res = await api.post<ApiResponse<WearableDevice>>("/api/wearable/devices/register/", data);
    return res.data;
  },

  async verifyDevice(id: number, pairing_token: string) {
    const res = await api.post<ApiResponse<null>>(`/api/wearable/devices/${id}/verify/`, { pairing_token });
    return res.data;
  },

  async listReadings(params?: { patient?: number; reading_type?: string; is_abnormal?: boolean }) {
    const res = await api.get<ApiResponse<DeviceReading[]>>("/api/wearable/readings/", { params });
    return res.data;
  },

  async ingestReading(data: {
    device_id: number; patient_id: number; reading_type: string;
    value: number; unit?: string; recorded_at?: string;
  }) {
    const res = await api.post<ApiResponse<DeviceReading>>("/api/wearable/readings/ingest/", data);
    return res.data;
  },

  async bulkIngest(readings: Array<{
    device_id: number; patient_id: number; reading_type: string;
    value: number; unit?: string;
  }>) {
    const res = await api.post<ApiResponse<{ ingested: number; readings: DeviceReading[] }>>(
      "/api/wearable/readings/bulk-ingest/", { readings },
    );
    return res.data;
  },

  async getPatientReadings(patient_id: number) {
    const res = await api.get<ApiResponse<Record<string, { value: number; unit: string }>>>(
      `/api/wearable/patients/${patient_id}/readings/`,
    );
    return res.data;
  },
};
