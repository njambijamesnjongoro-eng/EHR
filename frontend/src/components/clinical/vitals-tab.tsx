"use client";

import { useState } from "react";
import { clinicalApi } from "@/lib/api/clinical";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { VitalSignRecord, Patient, Visit } from "@/lib/types";

interface VitalsTabProps {
  patient: Patient;
  visits: Visit[];
  vitals: VitalSignRecord[];
  isLoading: boolean;
  onRefresh: () => void;
}

export default function VitalsTab({ patient, visits, vitals, isLoading, onRefresh }: VitalsTabProps) {
  const activeVisit = visits.find((v) => v.status === "in_progress");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    visit: activeVisit?.id || 0,
    patient: patient.id,
    temperature: "",
    blood_pressure_systolic: "",
    blood_pressure_diastolic: "",
    pulse_rate: "",
    respiratory_rate: "",
    oxygen_saturation: "",
    weight: "",
    height: "",
    notes: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!form.visit) {
      setError("An active visit is required to record vitals. Start a visit first.");
      return;
    }
    setIsSubmitting(true);
    try {
      await clinicalApi.createVitals(form as any);
      setShowForm(false);
      onRefresh();
    } catch {
      setError("Failed to record vitals");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Vital Signs</h3>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary text-sm">
          {showForm ? "Cancel" : "Record Vitals"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="card border-2 border-green-200 space-y-4">
          <h4 className="font-medium text-gray-900">Record Vital Signs</h4>
          {!activeVisit && (
            <div className="bg-amber-50 border border-amber-200 text-amber-700 px-4 py-3 rounded-lg text-sm">
              No active visit found. Please start a visit first.
            </div>
          )}
          <div>
            <label className="label">Select Visit</label>
            <select
              name="visit"
              value={form.visit}
              onChange={handleChange}
              className="select-field"
              required
            >
              <option value={0}>-- Select a visit --</option>
              {visits.map((v) => (
                <option key={v.id} value={v.id}>
                  {new Date(v.visit_date).toLocaleDateString()} - {v.status} - {v.chief_complaint?.slice(0, 40)}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="label">Temperature (°C)</label>
              <input
                type="number" step="0.1" name="temperature"
                value={form.temperature} onChange={handleChange}
                className="input-field" placeholder="37.0"
              />
            </div>
            <div>
              <label className="label">Systolic BP (mmHg)</label>
              <input
                type="number" name="blood_pressure_systolic"
                value={form.blood_pressure_systolic} onChange={handleChange}
                className="input-field" placeholder="120"
              />
            </div>
            <div>
              <label className="label">Diastolic BP (mmHg)</label>
              <input
                type="number" name="blood_pressure_diastolic"
                value={form.blood_pressure_diastolic} onChange={handleChange}
                className="input-field" placeholder="80"
              />
            </div>
            <div>
              <label className="label">Pulse Rate (bpm)</label>
              <input
                type="number" name="pulse_rate"
                value={form.pulse_rate} onChange={handleChange}
                className="input-field" placeholder="72"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="label">Respiratory Rate</label>
              <input
                type="number" name="respiratory_rate"
                value={form.respiratory_rate} onChange={handleChange}
                className="input-field" placeholder="16"
              />
            </div>
            <div>
              <label className="label">O2 Saturation (%)</label>
              <input
                type="number" step="0.1" name="oxygen_saturation"
                value={form.oxygen_saturation} onChange={handleChange}
                className="input-field" placeholder="98"
              />
            </div>
            <div>
              <label className="label">Weight (kg)</label>
              <input
                type="number" step="0.1" name="weight"
                value={form.weight} onChange={handleChange}
                className="input-field" placeholder="70"
              />
            </div>
            <div>
              <label className="label">Height (cm)</label>
              <input
                type="number" step="0.1" name="height"
                value={form.height} onChange={handleChange}
                className="input-field" placeholder="170"
              />
            </div>
          </div>
          <div>
            <label className="label">Notes</label>
            <textarea
              name="notes" rows={2}
              value={form.notes} onChange={handleChange}
              className="input-field"
            />
          </div>
          <div className="flex justify-end">
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              {isSubmitting ? <LoadingSpinner size="sm" /> : "Save Vitals"}
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <LoadingSpinner />
      ) : vitals.length === 0 ? (
        <p className="text-gray-500 text-sm py-4">No vital signs recorded.</p>
      ) : (
        <div className="space-y-3">
          {vitals.map((v) => (
            <div key={v.id} className="border border-gray-200 rounded-lg p-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {v.temperature && <div><span className="text-gray-500">Temp:</span> <span className="font-medium">{v.temperature} °C</span></div>}
                {v.blood_pressure_systolic && <div><span className="text-gray-500">BP:</span> <span className="font-medium">{v.blood_pressure_systolic}/{v.blood_pressure_diastolic} mmHg</span></div>}
                {v.pulse_rate && <div><span className="text-gray-500">Pulse:</span> <span className="font-medium">{v.pulse_rate} bpm</span></div>}
                {v.respiratory_rate && <div><span className="text-gray-500">RR:</span> <span className="font-medium">{v.respiratory_rate} /min</span></div>}
                {v.oxygen_saturation && <div><span className="text-gray-500">SpO2:</span> <span className="font-medium">{v.oxygen_saturation}%</span></div>}
                {v.weight && <div><span className="text-gray-500">Weight:</span> <span className="font-medium">{v.weight} kg</span></div>}
                {v.height && <div><span className="text-gray-500">Height:</span> <span className="font-medium">{v.height} cm</span></div>}
                {v.bmi && <div><span className="text-gray-500">BMI:</span> <span className="font-medium">{v.bmi}</span></div>}
              </div>
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
                <span className="text-xs text-gray-400">
                  {v.recorded_by_name && `By ${v.recorded_by_name}`} &middot; {new Date(v.recorded_at).toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
