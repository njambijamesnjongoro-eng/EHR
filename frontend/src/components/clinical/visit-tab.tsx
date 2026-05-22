"use client";

import { useState } from "react";
import { clinicalApi } from "@/lib/api/clinical";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { Visit, VisitFormData, Patient } from "@/lib/types";

interface VisitTabProps {
  patient: Patient;
  visits: Visit[];
  isLoading: boolean;
  onRefresh: () => void;
}

export default function VisitTab({ patient, visits, isLoading, onRefresh }: VisitTabProps) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<VisitFormData>({
    patient: patient.id,
    chief_complaint: "",
    symptoms: "",
    diagnosis_summary: "",
    treatment_plan: "",
    follow_up_date: "",
    notes: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await clinicalApi.createVisit(form);
      setShowForm(false);
      setForm({
        patient: patient.id, chief_complaint: "", symptoms: "",
        diagnosis_summary: "", treatment_plan: "", follow_up_date: "", notes: "",
      });
      onRefresh();
    } catch {
      setError("Failed to create visit");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCloseVisit = async (id: number) => {
    try {
      await clinicalApi.closeVisit(id);
      onRefresh();
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Patient Visits</h3>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary text-sm">
          {showForm ? "Cancel" : "Start New Visit"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="card border-2 border-primary-200 space-y-4">
          <h4 className="font-medium text-gray-900">New Visit / Encounter</h4>
          <div>
            <label className="label">Chief Complaint *</label>
            <textarea
              name="chief_complaint"
              required
              rows={2}
              value={form.chief_complaint}
              onChange={handleChange}
              className="input-field"
              placeholder="Patient's main reason for visit"
            />
          </div>
          <div>
            <label className="label">Symptoms</label>
            <textarea
              name="symptoms"
              rows={3}
              value={form.symptoms}
              onChange={handleChange}
              className="input-field"
              placeholder="Describe symptoms (comma-separated)"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Diagnosis Summary</label>
              <textarea
                name="diagnosis_summary"
                rows={2}
                value={form.diagnosis_summary}
                onChange={handleChange}
                className="input-field"
              />
            </div>
            <div>
              <label className="label">Treatment Plan</label>
              <textarea
                name="treatment_plan"
                rows={2}
                value={form.treatment_plan}
                onChange={handleChange}
                className="input-field"
              />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Follow-up Date</label>
              <input
                type="date"
                name="follow_up_date"
                value={form.follow_up_date}
                onChange={handleChange}
                className="input-field"
              />
            </div>
            <div>
              <label className="label">Notes</label>
              <textarea
                name="notes"
                rows={2}
                value={form.notes}
                onChange={handleChange}
                className="input-field"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              {isSubmitting ? <LoadingSpinner size="sm" /> : "Start Visit"}
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <LoadingSpinner />
      ) : visits.length === 0 ? (
        <p className="text-gray-500 text-sm py-4">No visits recorded.</p>
      ) : (
        <div className="space-y-3">
          {visits.map((visit) => (
            <div key={visit.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-900">
                      {new Date(visit.visit_date).toLocaleDateString("en-US", {
                        weekday: "short", year: "numeric", month: "short", day: "numeric",
                        hour: "2-digit", minute: "2-digit",
                      })}
                    </span>
                    <span className={`badge ${
                      visit.status === "completed" ? "badge-success" :
                      visit.status === "in_progress" ? "badge-info" :
                      visit.status === "cancelled" ? "badge-danger" : "badge-warning"
                    }`}>
                      {visit.status.replace("_", " ")}
                    </span>
                  </div>
                  {visit.doctor_name && (
                    <p className="text-xs text-gray-500 mt-1">Dr. {visit.doctor_name}</p>
                  )}
                </div>
                {visit.status === "in_progress" && (
                  <button
                    onClick={() => handleCloseVisit(visit.id)}
                    className="text-xs btn-secondary py-1 px-3"
                  >
                    Close Visit
                  </button>
                )}
              </div>
              {visit.chief_complaint && (
                <p className="text-sm text-gray-700 mt-2">
                  <span className="font-medium">Complaint:</span> {visit.chief_complaint}
                </p>
              )}
              {visit.symptoms && (
                <p className="text-sm text-gray-600 mt-1">
                  <span className="font-medium">Symptoms:</span> {visit.symptoms}
                </p>
              )}
              {visit.follow_up_date && (
                <p className="text-xs text-amber-600 mt-2">
                  Follow-up: {new Date(visit.follow_up_date).toLocaleDateString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
