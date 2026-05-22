"use client";

import { useState } from "react";
import { clinicalApi } from "@/lib/api/clinical";
import { labApi } from "@/lib/api/labs";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { Patient, Visit, LabRequest } from "@/lib/types";

interface LabsTabProps {
  patient: Patient;
  visits: Visit[];
  labRequests: LabRequest[];
  isLoading: boolean;
  onRefresh: () => void;
}

export default function LabsTab({ patient, visits, labRequests, isLoading, onRefresh }: LabsTabProps) {
  const activeVisit = visits.find((v) => v.status === "in_progress");
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [showResultForm, setShowResultForm] = useState<number | null>(null);
  const [form, setForm] = useState({
    visit: activeVisit?.id || 0,
    patient: patient.id,
    test_name: "",
    priority: "routine" as const,
    clinical_notes: "",
  });
  const [resultForm, setResultForm] = useState({
    result_text: "",
    remarks: "",
    is_abnormal: false,
  });
  const [resultFile, setResultFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!form.visit) {
      setError("An active visit is required.");
      return;
    }
    setIsSubmitting(true);
    try {
      await labApi.createRequest(form);
      setShowRequestForm(false);
      setForm({ visit: activeVisit?.id || 0, patient: patient.id, test_name: "", priority: "routine", clinical_notes: "" });
      onRefresh();
    } catch {
      setError("Failed to create lab request");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResultSubmit = async (e: React.FormEvent, labRequestId: number) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("lab_request", String(labRequestId));
      fd.append("result_text", resultForm.result_text);
      fd.append("remarks", resultForm.remarks);
      fd.append("is_abnormal", String(resultForm.is_abnormal));
      if (resultFile) fd.append("file_attachment", resultFile);
      await labApi.uploadResult(fd);
      setShowResultForm(null);
      setResultForm({ result_text: "", remarks: "", is_abnormal: false });
      setResultFile(null);
      onRefresh();
    } catch {
      setError("Failed to upload result");
    } finally {
      setIsSubmitting(false);
    }
  };

  const statusColors: Record<string, string> = {
    requested: "badge-warning",
    sample_collected: "badge-info",
    in_progress: "badge-info",
    completed: "badge-success",
    cancelled: "badge-danger",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Lab Tests</h3>
        <button onClick={() => setShowRequestForm(!showRequestForm)} className="btn-primary text-sm">
          {showRequestForm ? "Cancel" : "Request Lab Test"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {showRequestForm && (
        <form onSubmit={handleRequestSubmit} className="card border-2 border-amber-200 space-y-4">
          <h4 className="font-medium text-gray-900">New Lab Request</h4>
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
              <label className="label">Test Name *</label>
              <input
                type="text" name="test_name" required
                value={form.test_name} onChange={handleChange}
                className="input-field" placeholder="e.g. Complete Blood Count"
                list="common-tests"
              />
              <datalist id="common-tests">
                <option value="Complete Blood Count (CBC)" />
                <option value="Basic Metabolic Panel (BMP)" />
                <option value="Comprehensive Metabolic Panel (CMP)" />
                <option value="Lipid Panel" />
                <option value="Thyroid Function Test (TFT)" />
                <option value="Urinalysis" />
                <option value="Blood Culture" />
                <option value="Chest X-Ray" />
                <option value="ECG / EKG" />
                <option value="Liver Function Test (LFT)" />
                <option value="Renal Function Test (RFT)" />
                <option value="HbA1c" />
                <option value="Blood Glucose" />
                <option value="COVID-19 PCR" />
                <option value="Malaria Parasite" />
              </datalist>
            </div>
            <div>
              <label className="label">Priority</label>
              <select name="priority" value={form.priority} onChange={handleChange} className="select-field">
                <option value="routine">Routine</option>
                <option value="urgent">Urgent</option>
                <option value="stat">STAT</option>
              </select>
            </div>
          </div>
          <div>
            <label className="label">Clinical Notes</label>
            <textarea
              name="clinical_notes" rows={2}
              value={form.clinical_notes} onChange={handleChange}
              className="input-field"
              placeholder="Reason for test, specific clinical questions"
            />
          </div>
          <div className="flex justify-end">
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              {isSubmitting ? <LoadingSpinner size="sm" /> : "Request Test"}
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <LoadingSpinner />
      ) : labRequests.length === 0 ? (
        <p className="text-gray-500 text-sm py-4">No lab tests requested.</p>
      ) : (
        <div className="space-y-3">
          {labRequests.map((lab) => (
            <div key={lab.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <h4 className="font-medium text-gray-900">{lab.test_name}</h4>
                    <span className={`badge ${statusColors[lab.status] || "badge-info"}`}>
                      {lab.status.replace("_", " ")}
                    </span>
                    <span className={`badge ${lab.priority === "stat" ? "badge-danger" : lab.priority === "urgent" ? "badge-warning" : "badge-info"}`}>
                      {lab.priority}
                    </span>
                  </div>
                  {lab.clinical_notes && <p className="text-sm text-gray-600 mt-1">{lab.clinical_notes}</p>}
                  <p className="text-xs text-gray-400 mt-1">
                    {lab.requested_by_name && `Dr. ${lab.requested_by_name}`}
                    {" - "}{new Date(lab.requested_at).toLocaleString()}
                  </p>
                </div>
                {lab.status === "requested" && (
                  <button
                    onClick={() => setShowResultForm(showResultForm === lab.id ? null : lab.id)}
                    className="btn-primary text-xs py-1.5 px-3"
                  >
                    {showResultForm === lab.id ? "Cancel" : "Upload Result"}
                  </button>
                )}
              </div>

              {showResultForm === lab.id && (
                <form
                  onSubmit={(e) => handleResultSubmit(e, lab.id)}
                  className="mt-4 pt-4 border-t border-gray-200 space-y-3"
                >
                  <h5 className="text-sm font-medium text-gray-700">Upload Results for {lab.test_name}</h5>
                  <div>
                    <label className="label">Result Text</label>
                    <textarea
                      name="result_text" rows={3}
                      value={resultForm.result_text}
                      onChange={(e) => setResultForm((p) => ({ ...p, result_text: e.target.value }))}
                      className="input-field"
                    />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="label">Remarks</label>
                      <textarea
                        name="remarks" rows={2}
                        value={resultForm.remarks}
                        onChange={(e) => setResultForm((p) => ({ ...p, remarks: e.target.value }))}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="label">Attachment (PDF/Image)</label>
                      <input
                        type="file" accept=".pdf,.jpg,.jpeg,.png"
                        onChange={(e) => setResultFile(e.target.files?.[0] || null)}
                        className="input-field"
                      />
                    </div>
                  </div>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={resultForm.is_abnormal}
                      onChange={(e) => setResultForm((p) => ({ ...p, is_abnormal: e.target.checked }))}
                      className="rounded border-gray-300 text-red-600"
                    />
                    <span className="text-sm text-gray-700">Mark as abnormal</span>
                  </label>
                  <div className="flex justify-end">
                    <button type="submit" disabled={isSubmitting} className="btn-primary text-sm">
                      {isSubmitting ? <LoadingSpinner size="sm" /> : "Upload Result"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
