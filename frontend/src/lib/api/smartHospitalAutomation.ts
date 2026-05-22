import api from "../api";
import type { ApiResponse, SmartDeviceEvent, DeviceHealth, HospitalIoTSummary, PatientFlowAnalysis, Bottleneck, PredictiveStaffing } from "../types";

export const smartHospitalAutomationApi = {
  async listDeviceEvents(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<SmartDeviceEvent[]>>("/api/smart-hospital/device-events/", { params });
    return res.data;
  },

  async deviceEventDetail(id: number) {
    const res = await api.get<ApiResponse<SmartDeviceEvent>>(`/api/smart-hospital/device-events/${id}/`);
    return res.data;
  },

  async ingestEvent(data: Record<string, unknown>) {
    const res = await api.post<ApiResponse<SmartDeviceEvent>>("/api/smart-hospital/device-events/ingest/", data);
    return res.data;
  },

  async deviceHealth(device_id: number) {
    const res = await api.get<ApiResponse<DeviceHealth>>(`/api/smart-hospital/devices/${device_id}/health/`);
    return res.data;
  },

  async iotSummary(hospital_id?: number) {
    const res = await api.get<ApiResponse<HospitalIoTSummary>>("/api/smart-hospital/iot-summary/", {
      params: { hospital_id },
    });
    return res.data;
  },

  async patientFlow(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<PatientFlowAnalysis>>("/api/smart-hospital/automation/patient-flow/", { params });
    return res.data;
  },

  async bottlenecks(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Bottleneck[]>>("/api/smart-hospital/automation/bottlenecks/", { params });
    return res.data;
  },

  async staffing(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<PredictiveStaffing>>("/api/smart-hospital/automation/staffing/", { params });
    return res.data;
  },

  async equipmentUtilization(params?: Record<string, string | number>) {
    const res = await api.get<ApiResponse<Record<string, unknown>>>("/api/smart-hospital/automation/equipment/", { params });
    return res.data;
  },
};
