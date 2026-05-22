import api from "../api";
import type {
  Visit,
  VisitFormData,
  VitalSignRecord,
  VitalSignFormData,
  Diagnosis,
  DiagnosisFormData,
  Prescription,
  PrescriptionFormData,
  ApiResponse,
} from "../types";

export const clinicalApi = {
  // ─── Visits ───
  async listVisits(params?: {
    page?: number;
    patient?: number;
    status?: string;
    search?: string;
  }) {
    const response = await api.get<ApiResponse<Visit[]>>(
      "/api/clinical/visits/",
      { params }
    );
    return response.data;
  },

  async getVisit(id: number) {
    const response = await api.get<ApiResponse<Visit>>(
      `/api/clinical/visits/${id}/`
    );
    return response.data;
  },

  async createVisit(data: VisitFormData) {
    const response = await api.post<ApiResponse<Visit>>(
      "/api/clinical/visits/",
      data
    );
    return response.data;
  },

  async updateVisit(id: number, data: Partial<VisitFormData>) {
    const response = await api.patch<ApiResponse<Visit>>(
      `/api/clinical/visits/${id}/`,
      data
    );
    return response.data;
  },

  async closeVisit(id: number) {
    const response = await api.post<ApiResponse<null>>(
      `/api/clinical/visits/${id}/close/`
    );
    return response.data;
  },

  async getVisitTimeline(id: number) {
    const response = await api.get<ApiResponse<unknown[]>>(
      `/api/clinical/visits/${id}/timeline/`
    );
    return response.data;
  },

  // ─── Vital Signs ───
  async listVitals(params?: { patient?: number; visit?: number }) {
    const response = await api.get<ApiResponse<VitalSignRecord[]>>(
      "/api/clinical/vitals/",
      { params }
    );
    return response.data;
  },

  async createVitals(data: VitalSignFormData) {
    const response = await api.post<ApiResponse<VitalSignRecord>>(
      "/api/clinical/vitals/",
      data
    );
    return response.data;
  },

  // ─── Diagnoses ───
  async listDiagnoses(params?: {
    patient?: number;
    visit?: number;
    search?: string;
  }) {
    const response = await api.get<ApiResponse<Diagnosis[]>>(
      "/api/clinical/diagnoses/",
      { params }
    );
    return response.data;
  },

  async createDiagnosis(data: DiagnosisFormData) {
    const response = await api.post<ApiResponse<Diagnosis>>(
      "/api/clinical/diagnoses/",
      data
    );
    return response.data;
  },

  async updateDiagnosis(id: number, data: Partial<DiagnosisFormData>) {
    const response = await api.patch<ApiResponse<Diagnosis>>(
      `/api/clinical/diagnoses/${id}/`,
      data
    );
    return response.data;
  },

  // ─── Prescriptions ───
  async listPrescriptions(params?: {
    patient?: number;
    visit?: number;
    is_active?: boolean;
  }) {
    const response = await api.get<ApiResponse<Prescription[]>>(
      "/api/clinical/prescriptions/",
      { params }
    );
    return response.data;
  },

  async createPrescription(data: PrescriptionFormData) {
    const response = await api.post<ApiResponse<Prescription>>(
      "/api/clinical/prescriptions/",
      data
    );
    return response.data;
  },

  async dispensePrescriptions(ids: number[]) {
    const response = await api.post<ApiResponse<null>>(
      "/api/clinical/prescriptions/dispense/",
      { prescription_ids: ids }
    );
    return response.data;
  },
};
