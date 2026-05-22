"use client";

import { useEffect, useState } from "react";
import { billingApi } from "@/lib/api/billing";
import { patientApi } from "@/lib/api/patients";
import { useAuth } from "@/lib/auth-context";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { Invoice, InvoiceFormData, Patient } from "@/lib/types";

type FilterStatus = "all" | "pending" | "paid" | "partially_paid";

export default function BillingPage() {
  const { user } = useAuth();
  const canManage = !!(user && ["super_admin", "hospital_admin", "receptionist"].includes(user.role));

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterStatus>("all");
  const [showCreate, setShowCreate] = useState(false);
  const [payInvoiceId, setPayInvoiceId] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    loadInvoices();
  }, [filter]);

  async function loadInvoices() {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filter !== "all") params.status = filter;
      if (searchTerm) params.search = searchTerm;
      const res = await billingApi.listInvoices(params);
      setInvoices((res.results ?? res.data ?? []) as Invoice[]);
    } catch (e) {
      console.error("Failed to load invoices", e);
    } finally {
      setLoading(false);
    }
  }

  const stats = {
    total: invoices.reduce((s, i) => s + parseFloat(i.total_amount || "0"), 0),
    paid: invoices.filter((i) => i.status === "paid").reduce((s, i) => s + parseFloat(i.total_amount || "0"), 0),
    pending: invoices.filter((i) => i.status === "pending" || i.status === "partially_paid").reduce((s, i) => s + parseFloat(i.balance || "0"), 0),
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Billing & Invoices</h1>
          <p className="text-sm text-gray-500 mt-1">Manage patient invoices and payments</p>
        </div>
        {canManage && (
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            New Invoice
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Total Billable</p>
          <p className="text-2xl font-bold text-gray-900">KES {stats.total.toLocaleString()}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Total Collected</p>
          <p className="text-2xl font-bold text-green-600">KES {stats.paid.toLocaleString()}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Outstanding</p>
          <p className="text-2xl font-bold text-red-600">KES {stats.pending.toLocaleString()}</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex space-x-2">
          {(["all", "pending", "paid", "partially_paid"] as FilterStatus[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-sm rounded-lg font-medium transition-colors ${
                filter === f
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              {f.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Search patient..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input flex-1 max-w-xs"
          onKeyDown={(e) => e.key === "Enter" && loadInvoices()}
        />
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <InvoiceTable
          invoices={invoices}
          onRefresh={loadInvoices}
          canManage={canManage}
          onPay={(id) => setPayInvoiceId(id)}
        />
      )}

      {showCreate && canManage && (
        <CreateInvoiceModal
          onClose={() => setShowCreate(false)}
          onSuccess={() => { setShowCreate(false); loadInvoices(); }}
        />
      )}

      {payInvoiceId && canManage && (
        <PaymentModal
          invoiceId={payInvoiceId}
          onClose={() => setPayInvoiceId(null)}
          onSuccess={() => { setPayInvoiceId(null); loadInvoices(); }}
        />
      )}
    </div>
  );
}

function InvoiceTable({
  invoices, onRefresh, canManage, onPay,
}: {
  invoices: Invoice[]; onRefresh: () => void; canManage?: boolean; onPay: (id: number) => void;
}) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (invoices.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">No invoices found</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-medium text-gray-600">Invoice #</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Patient</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">Total</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">Paid</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">Balance</th>
              <th className="text-center px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {invoices.map((inv) => (
              <>
                <tr key={inv.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setExpanded(expanded === inv.id ? null : inv.id)}>
                  <td className="px-4 py-3 font-medium text-gray-900">{inv.invoice_number}</td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-gray-900">{inv.patient_name}</p>
                      <p className="text-xs text-gray-400">{inv.patient_health_id}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-medium">KES {parseFloat(inv.total_amount).toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-green-600">KES {parseFloat(inv.amount_paid).toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-red-600">KES {parseFloat(inv.balance).toLocaleString()}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      inv.status === "paid" ? "bg-green-50 text-green-700" :
                      inv.status === "partially_paid" ? "bg-yellow-50 text-yellow-700" :
                      inv.status === "cancelled" ? "bg-red-50 text-red-700" :
                      "bg-gray-50 text-gray-700"
                    }`}>
                      {inv.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {canManage && inv.status !== "paid" && inv.status !== "cancelled" && (
                      <button
                        onClick={(e) => { e.stopPropagation(); onPay(inv.id); }}
                        className="text-primary-600 hover:text-primary-800 text-sm font-medium"
                      >
                        Record Payment
                      </button>
                    )}
                  </td>
                </tr>
                {expanded === inv.id && (
                  <tr key={`${inv.id}-details`}>
                    <td colSpan={7} className="px-4 py-3 bg-gray-50">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        {[
                          { label: "Consultation", value: inv.consultation_fee },
                          { label: "Lab", value: inv.lab_fee },
                          { label: "Pharmacy", value: inv.pharmacy_fee },
                          { label: "Admission", value: inv.admission_fee },
                          { label: "Radiology", value: inv.radiology_fee },
                          { label: "Other", value: inv.other_fees },
                          { label: "Discount", value: `-${inv.discount}` },
                          { label: "Tax", value: inv.tax },
                        ].map((item) => (
                          <div key={item.label}>
                            <span className="text-gray-500">{item.label}</span>
                            <p className="font-medium">KES {parseFloat(item.value || "0").toLocaleString()}</p>
                          </div>
                        ))}
                      </div>
                      {inv.payments && inv.payments.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <p className="text-sm font-medium text-gray-700 mb-2">Payments</p>
                          {inv.payments.map((p) => (
                            <div key={p.id} className="flex justify-between text-sm">
                              <span className="text-gray-500">{p.payment_method} - {new Date(p.payment_date).toLocaleDateString()}</span>
                              <span className="font-medium">KES {parseFloat(p.amount_paid).toLocaleString()}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CreateInvoiceModal({
  onClose, onSuccess,
}: {
  onClose: () => void; onSuccess: () => void;
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [form, setForm] = useState<InvoiceFormData>({
    patient: 0, consultation_fee: "0", lab_fee: "0", pharmacy_fee: "0",
    admission_fee: "0", radiology_fee: "0", other_fees: "0",
    discount: "0", tax: "0", insurance_provider: "", insurance_policy_no: "", notes: "",
  });
  const [submitting, setSubmitting] = useState(false);

  async function searchPatients(term: string) {
    setSearchTerm(term);
    if (term.length < 2) return;
    try {
      const res = await patientApi.quickSearch(term);
      setPatients(res.data ?? []);
    } catch {
      setPatients([]);
    }
  }

  function updateField(field: keyof typeof form, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit() {
    if (!form.patient) return;
    setSubmitting(true);
    try {
      await billingApi.createInvoice(form);
      onSuccess();
    } catch (e) {
      console.error("Create invoice failed", e);
    } finally {
      setSubmitting(false);
    }
  }

  const feeFields: { key: keyof typeof form; label: string }[] = [
    { key: "consultation_fee", label: "Consultation Fee" },
    { key: "lab_fee", label: "Lab Fee" },
    { key: "pharmacy_fee", label: "Pharmacy Fee" },
    { key: "admission_fee", label: "Admission Fee" },
    { key: "radiology_fee", label: "Radiology Fee" },
    { key: "other_fees", label: "Other Fees" },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">New Invoice</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
            <input
              type="text"
              placeholder="Search patient..."
              value={searchTerm}
              onChange={(e) => searchPatients(e.target.value)}
              className="input w-full"
            />
            {patients.length > 0 && (
              <div className="mt-1 border border-gray-200 rounded-lg max-h-40 overflow-y-auto">
                {patients.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => { updateField("patient", p.id); setSearchTerm(`${p.first_name} ${p.last_name} (${p.health_id})`); setPatients([]); }}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 text-sm"
                  >
                    {p.first_name} {p.last_name} <span className="text-gray-400">{p.health_id}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            {feeFields.map((field) => (
              <div key={field.key}>
                <label className="block text-sm font-medium text-gray-700 mb-1">{field.label}</label>
                <input
                  type="number"
                  min="0"
                  value={form[field.key]}
                  onChange={(e) => updateField(field.key, e.target.value)}
                  className="input w-full"
                />
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Discount</label>
              <input
                type="number"
                min="0"
                value={form.discount}
                onChange={(e) => updateField("discount", e.target.value)}
                className="input w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tax</label>
              <input
                type="number"
                min="0"
                value={form.tax}
                onChange={(e) => updateField("tax", e.target.value)}
                className="input w-full"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Insurance Provider</label>
              <input
                type="text"
                value={form.insurance_provider}
                onChange={(e) => updateField("insurance_provider", e.target.value)}
                className="input w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Policy No.</label>
              <input
                type="text"
                value={form.insurance_policy_no}
                onChange={(e) => updateField("insurance_policy_no", e.target.value)}
                className="input w-full"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => updateField("notes", e.target.value)}
              className="input w-full"
              rows={2}
            />
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSubmit} disabled={!form.patient || submitting} className="btn-primary">
            {submitting ? "Creating..." : "Create Invoice"}
          </button>
        </div>
      </div>
    </div>
  );
}

function PaymentModal({
  invoiceId, onClose, onSuccess,
}: {
  invoiceId: number; onClose: () => void; onSuccess: () => void;
}) {
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("cash");
  const [reference, setReference] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    if (!amount || parseFloat(amount) <= 0) return;
    setSubmitting(true);
    try {
      await billingApi.recordPayment({
        invoice: invoiceId,
        amount_paid: amount,
        payment_method: method,
        transaction_reference: reference || undefined,
        notes: notes || undefined,
      });
      onSuccess();
    } catch (e) {
      console.error("Payment failed", e);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Record Payment</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Amount (KES)</label>
            <input
              type="number"
              min="1"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="input w-full"
              placeholder="0.00"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
            <select value={method} onChange={(e) => setMethod(e.target.value)} className="input w-full">
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="mpesa">M-Pesa</option>
              <option value="insurance">Insurance</option>
              <option value="bank_transfer">Bank Transfer</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Transaction Reference (optional)</label>
            <input
              type="text"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="input w-full"
              rows={2}
            />
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSubmit} disabled={!amount || parseFloat(amount) <= 0 || submitting} className="btn-primary">
            {submitting ? "Recording..." : "Record Payment"}
          </button>
        </div>
      </div>
    </div>
  );
}
