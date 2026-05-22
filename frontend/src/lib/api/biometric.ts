import api from "../api";
import type { BiometricIdentity, ApiResponse } from "../types";

export const biometricApi = {
  async listIdentities(params?: { user?: number; biometric_type?: string }) {
    const res = await api.get<ApiResponse<BiometricIdentity[]>>("/api/biometric/identities/", { params });
    return res.data;
  },

  async registerBiometric(data: { biometric_type: string; encrypted_template: string; device_id?: string }) {
    const res = await api.post<ApiResponse<BiometricIdentity>>("/api/biometric/register/", data);
    return res.data;
  },

  async verifyBiometric(biometric_type: string, encrypted_template: string) {
    const res = await api.post<ApiResponse<null>>("/api/biometric/verify/", { biometric_type, encrypted_template });
    return res.data;
  },

  async deactivateBiometric(id: number) {
    const res = await api.post<ApiResponse<null>>(`/api/biometric/identities/${id}/deactivate/`);
    return res.data;
  },

  async getMyBiometrics() {
    const res = await api.get<ApiResponse<BiometricIdentity[]>>("/api/biometric/my-biometrics/");
    return res.data;
  },
};
