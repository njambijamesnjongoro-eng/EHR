"use client";

import { useState } from "react";
import { clinicalApi } from "@/lib/api/clinical";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { Prescription, Patient, Visit } from "@/lib/types";

interface PrescriptionTabProps {
  patient: Patient;
  visits: Visit[];
  prescriptions: Prescription[];
  isLoading: boolean;
  onRefresh: () => void;
}

const frequencies = [
  { value: "od", label: "Once Daily" },
  { value: "bd", label: "Twice Daily" },
  { value: "tds", label: "Three Times Daily" },
  { value: "qid", label: "Four Times Daily" },
  { value: "qhs", label: "At Bedtime" },
  { value: "prn", label: "As Needed" },
  { value: "stat", label: "Immediately" },
];

const routes = [
  { value: "oral", label: "Oral" },
  { value: "iv", label: "Intravenous" },
  { value: "im", label: "Intramuscular" },
  { value: "sc", label: "Subcutaneous" },
  { value: "topical", label: "Topical" },
  { value: "inhalation", label: "Inhalation" },
  { value: "sublingual", label: "Sublingual" },
];

export default function PrescriptionTab({ patient, visits, prescriptions, isLoading, onRefresh }: PrescriptionTabProps) {
  const activeVisit = visits.find((v) => v.status === "in_progress");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    visit: activeVisit?.id || 0,
    patient: patient.id,
    medication_name: "",
    dosage: "",
    frequency: "bd" as const,
    duration_days: 7,
    duration_text: "",
    route: "oral" as const,
    instructions: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [selectedRx, setSelectedRx] = useState<number[]>([]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.name === "duration_days" ? parseInt(e.target.value) || 0 : e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!form.visit) {
      setError("An active visit is required. Start a visit first.");
      return;
    }
    setIsSubmitting(true);
    try {
      await clinicalApi.createPrescription(form);
      setShowForm(false);
      onRefresh();
    } catch {
      setError("Failed to create prescription");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDispense = async () => {
    if (selectedRx.length === 0) return;
    try {
      await clinicalApi.dispensePrescriptions(selectedRx);
      setSelectedRx([]);
      onRefresh();
    } catch {
      // ignore
    }
  };

  const toggleRx = (id: number) => {
    setSelectedRx((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Prescriptions</h3>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary text-sm">
          {showForm ? "Cancel" : "Add Prescription"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="card border-2 border-purple-200 space-y-4">
          <h4 className="font-medium text-gray-900">New Prescription</h4>
          {!activeVisit && (
            <div className="bg-amber-50 border border-amber-200 text-amber-700 px-4 py-3 rounded-lg text-sm">
              No active visit. Please start a visit first.
            </div>
          )}
          <div>
            <label className="label">Visit</label>
            <select name="visit" value={form.visit} onChange={handleChange} className="select-field" required>
              <option value={0}>-- Select visit --</option>
              {visits.map((v) => (
                <option key={v.id} value={v.id}>
                  {new Date(v.visit_date).toLocaleDateString()} - {v.status}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="label">Medication Name *</label>
              <input
                type="text" name="medication_name" required
                value={form.medication_name} onChange={handleChange}
                className="input-field" placeholder="e.g. Amoxicillin"
              />
            </div>
            <div>
              <label className="label">Dosage *</label>
              <input
                type="text" name="dosage" required
                value={form.dosage} onChange={handleChange}
                className="input-field" placeholder="e.g. 500mg"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="label">Frequency</label>
              <select name="frequency" value={form.frequency} onChange={handleChange} className="select-field">
                {frequencies.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Route</label>
              <select name="route" value={form.route} onChange={handleChange} className="select-field">
                {routes.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Duration (days)</label>
              <input
                type="number" name="duration_days" min={1}
                value={form.duration_days} onChange={handleChange}
                className="input-field"
              />
            </div>
            <div>
              <label className="label">Duration (text)</label>
              <input
                type="text" name="duration_text"
                value={form.duration_text} onChange={handleChange}
                className="input-field" placeholder="e.g. 2 weeks"
              />
            </div>
          </div>
          <div>
            <label className="label">Instructions</label>
            <textarea
              name="instructions" rows={2}
              value={form.instructions} onChange={handleChange}
              className="input-field" placeholder="e.g. Take with food"
            />
          </div>
          <div className="flex justify-end">
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              {isSubmitting ? <LoadingSpinner size="sm" /> : "Prescribe"}
            </button>
          </div>
        </form>
      )}

      {selectedRx.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center justify-between">
          <span className="text-sm text-blue-700">{selectedRx.length} prescription(s) selected</span>
          <button onClick={handleDispense} className="btn-primary text-sm">
            Mark as Dispensed
          </button>
        </div>
      )}

      {isLoading ? (
        <LoadingSpinner />
      ) : prescriptions.length === 0 ? (
        <p className="text-gray-500 text-sm py-4">No prescriptions recorded.</p>
      ) : (
        <div className="space-y-3">
          {prescriptions.map((rx) => (
            <div key={rx.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  {!rx.is_dispensed && (
                    <input
                      type="checkbox"
                      checked={selectedRx.includes(rx.id)}
                      onChange={() => toggleRx(rx.id)}
                      className="rounded border-gray-300 text-primary-600 mt-1"
                    />
                  )}
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">{rx.medication_name}</h4>
                      <span className="text-sm text-gray-500">{rx.dosage}</span>
                      <span className={`badge ${rx.is_dispensed ? "badge-success" : "badge-warning"}`}>
                        {rx.is_dispensed ? "Dispensed" : "Pending"}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {frequencies.find((f) => f.value === rx.frequency)?.label || rx.frequency}
                      {" - "}
                      {routes.find((r) => r.value === rx.route)?.label || rx.route}
                      {rx.duration_days && ` - ${rx.duration_days} days`}
                    </p>
                    {rx.instructions && <p className="text-xs text-gray-500 mt-1">{rx.instructions}</p>}
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                {rx.prescribed_by_name && `Dr. ${rx.prescribed_by_name}`}
                {" - "}{new Date(rx.prescribed_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
