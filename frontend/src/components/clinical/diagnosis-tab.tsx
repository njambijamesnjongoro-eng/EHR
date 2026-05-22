"use client";

import { useState } from "react";
import { clinicalApi } from "@/lib/api/clinical";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { Diagnosis, Patient, Visit } from "@/lib/types";

interface DiagnosisTabProps {
  patient: Patient;
  visits: Visit[];
  diagnoses: Diagnosis[];
  isLoading: boolean;
  onRefresh: () => void;
}

const icdExampleCodes = [
  "A00", "A01", "E10", "E11", "I10", "I11", "J00", "J01", "J02",
  "J03", "J04", "J05", "J06", "J15", "J18", "J20", "J45", "K25",
  "K26", "K27", "M00", "M01", "M02", "M03", "M04", "M05", "N00",
];

const severityColors: Record<string, string> = {
  mild: "badge-success",
  moderate: "badge-warning",
  severe: "badge-danger",
  critical: "badge-danger",
};

export default function DiagnosisTab({ patient, visits, diagnoses, isLoading, onRefresh }: DiagnosisTabProps) {
  const activeVisit = visits.find((v) => v.status === "in_progress");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    visit: activeVisit?.id || 0,
    patient: patient.id,
    diagnosis_type: "primary" as const,
    diagnosis_name: "",
    icd_code: "",
    severity: "moderate" as const,
    clinical_notes: "",
    is_confirmed: false,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const value = e.target.type === "checkbox" ? (e.target as HTMLInputElement).checked : e.target.value;
    setForm((prev) => ({ ...prev, [e.target.name]: value }));
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
      await clinicalApi.createDiagnosis(form);
      setShowForm(false);
      onRefresh();
    } catch {
      setError("Failed to record diagnosis");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Diagnoses</h3>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary text-sm">
          {showForm ? "Cancel" : "Add Diagnosis"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="card border-2 border-blue-200 space-y-4">
          <h4 className="font-medium text-gray-900">Record Diagnosis</h4>
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Diagnosis Name *</label>
              <input
                type="text" name="diagnosis_name" required
                value={form.diagnosis_name} onChange={handleChange}
                className="input-field" placeholder="e.g. Type 2 Diabetes"
              />
            </div>
            <div>
              <label className="label">ICD Code</label>
              <input
                type="text" name="icd_code" list="icd-codes"
                value={form.icd_code} onChange={handleChange}
                className="input-field" placeholder="e.g. E11"
              />
              <datalist id="icd-codes">
                {icdExampleCodes.map((c) => <option key={c} value={c} />)}
              </datalist>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Type</label>
              <select name="diagnosis_type" value={form.diagnosis_type} onChange={handleChange} className="select-field">
                <option value="primary">Primary</option>
                <option value="secondary">Secondary</option>
              </select>
            </div>
            <div>
              <label className="label">Severity</label>
              <select name="severity" value={form.severity} onChange={handleChange} className="select-field">
                <option value="mild">Mild</option>
                <option value="moderate">Moderate</option>
                <option value="severe">Severe</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div className="flex items-end pb-3">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox" name="is_confirmed"
                  checked={form.is_confirmed} onChange={handleChange}
                  className="rounded border-gray-300 text-primary-600"
                />
                <span className="text-sm text-gray-700">Confirmed</span>
              </label>
            </div>
          </div>
          <div>
            <label className="label">Clinical Notes</label>
            <textarea
              name="clinical_notes" rows={3}
              value={form.clinical_notes} onChange={handleChange}
              className="input-field"
            />
          </div>
          <div className="flex justify-end">
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              {isSubmitting ? <LoadingSpinner size="sm" /> : "Save Diagnosis"}
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <LoadingSpinner />
      ) : diagnoses.length === 0 ? (
        <p className="text-gray-500 text-sm py-4">No diagnoses recorded.</p>
      ) : (
        <div className="space-y-3">
          {diagnoses.map((d) => (
            <div key={d.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <h4 className="font-medium text-gray-900">{d.diagnosis_name}</h4>
                  <span className={`badge ${severityColors[d.severity] || "badge-info"}`}>
                    {d.severity}
                  </span>
                  <span className={`badge ${d.diagnosis_type === "primary" ? "badge-info" : "badge-warning"}`}>
                    {d.diagnosis_type}
                  </span>
                  {d.is_confirmed && <span className="badge-success">Confirmed</span>}
                </div>
              </div>
              {d.icd_code && <p className="text-xs text-gray-500 mt-1">ICD: {d.icd_code}</p>}
              {d.clinical_notes && <p className="text-sm text-gray-600 mt-2">{d.clinical_notes}</p>}
              <p className="text-xs text-gray-400 mt-2">
                {d.diagnosed_by_name && `By Dr. ${d.diagnosed_by_name}`} &middot; {new Date(d.diagnosed_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
