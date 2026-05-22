import api from "../api";
import type { ApiResponse, TimelineEvent } from "../types";

export const timelineApi = {
  async getPatientTimeline(patientId: number) {
    const response = await api.get<ApiResponse<TimelineEvent[]>>(
      `/api/timeline/patient/${patientId}/`
    );
    return response.data;
  },
};
