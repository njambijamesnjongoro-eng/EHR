import api from "../api";
import type { Invoice, InvoiceFormData, PaymentRecord, ApiResponse } from "../types";

export const billingApi = {
  async listInvoices(params?: {
    page?: number; status?: string; patient?: number; search?: string;
  }) {
    const res = await api.get<ApiResponse<Invoice[]>>("/api/billing/invoices/", { params });
    return res.data;
  },

  async getInvoice(id: number) {
    const res = await api.get<ApiResponse<Invoice>>(`/api/billing/invoices/${id}/`);
    return res.data;
  },

  async createInvoice(data: InvoiceFormData) {
    const res = await api.post<ApiResponse<Invoice>>("/api/billing/invoices/", data);
    return res.data;
  },

  async listPayments(params?: { invoice?: number }) {
    const res = await api.get<ApiResponse<PaymentRecord[]>>("/api/billing/payments/", { params });
    return res.data;
  },

  async recordPayment(data: {
    invoice: number; amount_paid: string; payment_method: string;
    transaction_reference?: string; notes?: string;
  }) {
    const res = await api.post<ApiResponse<PaymentRecord>>("/api/billing/payments/", data);
    return res.data;
  },
};
