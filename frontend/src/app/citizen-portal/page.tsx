"use client";

import { useEffect, useState } from "react";
import { citizenPortalApi } from "@/lib/api/citizenPortal";
import LoadingSpinner from "@/components/ui/loading-spinner";

export default function CitizenPortalPage() {
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const res = await citizenPortalApi.getHealthSummary();
      setSummary((res.data ?? res) as Record<string, unknown>);
    } catch (e) {
      console.error("Failed to load health summary", e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  const patient = summary?.patient as Record<string, unknown> | undefined;
  const diagnoses = (summary?.diagnoses ?? []) as Array<Record<string, unknown>>;
  const activePrescriptions = (summary?.active_prescriptions ?? []) as Array<Record<string, unknown>>;
  const recentVisits = (summary?.recent_visits ?? []) as Array<Record<string, unknown>>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Health Portal</h1>
        <p className="text-sm text-gray-500 mt-1">Your personal health summary and records</p>
      </div>

      {patient && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-3">Personal Information</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-500">Name</p>
              <p className="font-medium">{patient.full_name as string}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Health ID</p>
              <p className="font-medium">{patient.health_id as string}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Gender</p>
              <p className="font-medium capitalize">{patient.gender as string}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Blood Group</p>
              <p className="font-medium">{patient.blood_group as string}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <h2 className="text-lg font-semibold mb-3">Recent Visits</h2>
          {recentVisits.length === 0 ? (
            <p className="text-sm text-gray-500">No recent visits</p>
          ) : (
            <div className="space-y-3">
              {recentVisits.slice(0, 5).map((v) => (
                <div key={v.id as number} className="p-2 bg-gray-50 rounded">
                  <p className="text-sm font-medium">{v.date as string}</p>
                  <p className="text-xs text-gray-600">{v.chief_complaint as string}</p>
                  <p className="text-xs text-gray-400">Dr. {v.doctor_name as string}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-3">Active Prescriptions</h2>
          {activePrescriptions.length === 0 ? (
            <p className="text-sm text-gray-500">No active prescriptions</p>
          ) : (
            <div className="space-y-3">
              {activePrescriptions.slice(0, 5).map((p, i) => (
                <div key={i} className="p-2 bg-blue-50 rounded">
                  <p className="text-sm font-medium">{p.medication_name as string}</p>
                  <p className="text-xs text-gray-600">{p.dosage as string} - {p.frequency as string}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Diagnoses</h2>
        {diagnoses.length === 0 ? (
          <p className="text-sm text-gray-500">No diagnoses recorded</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b">
                  <th className="text-left px-3 py-2 text-gray-600 font-medium">Diagnosis</th>
                  <th className="text-left px-3 py-2 text-gray-600 font-medium">ICD Code</th>
                  <th className="text-left px-3 py-2 text-gray-600 font-medium">Severity</th>
                  <th className="text-right px-3 py-2 text-gray-600 font-medium">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {diagnoses.map((d, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium">{d.name as string}</td>
                    <td className="px-3 py-2 text-gray-600">{d.icd_code as string}</td>
                    <td className="px-3 py-2 capitalize">{d.severity as string}</td>
                    <td className="px-3 py-2 text-right text-gray-500">{d.date as string}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
