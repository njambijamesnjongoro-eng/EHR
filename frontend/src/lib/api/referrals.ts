import api from "../api";
import type { Referral, ApiResponse } from "../types";

export const referralApi = {
  async list(params?: { status?: string; priority?: string; receiving_hospital?: number }) {
    const res = await api.get<ApiResponse<Referral[]>>("/api/referrals/referrals/", { params });
    return res.data;
  },

  async get(id: number) {
    const res = await api.get<ApiResponse<Referral>>(`/api/referrals/referrals/${id}/`);
    return res.data;
  },

  async create(data: {
    patient: number; receiving_hospital: number; priority: string;
    clinical_summary: string; reason_for_referral: string; referral_notes?: string;
  }) {
    const res = await api.post<ApiResponse<Referral>>("/api/referrals/referrals/", data);
    return res.data;
  },

  async accept(id: number, response_notes?: string) {
    const res = await api.post<ApiResponse<null>>(`/api/referrals/referrals/${id}/accept/`, { response_notes });
    return res.data;
  },

  async decline(id: number, response_notes?: string) {
    const res = await api.post<ApiResponse<null>>(`/api/referrals/referrals/${id}/decline/`, { response_notes });
    return res.data;
  },

  async complete(id: number) {
    const res = await api.post<ApiResponse<null>>(`/api/referrals/referrals/${id}/complete/`);
    return res.data;
  },
};
