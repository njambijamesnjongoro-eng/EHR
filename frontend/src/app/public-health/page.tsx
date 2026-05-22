"use client";

import { useEffect, useState } from "react";
import { publicHealthApi } from "@/lib/api/publicHealth";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { OutbreakSignal } from "@/lib/types";

export default function PublicHealthPage() {
  const [signals, setSignals] = useState<OutbreakSignal[]>([]);
  const [burden, setBurden] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [sRes, bRes] = await Promise.all([
        publicHealthApi.getOutbreakSignals(14),
        publicHealthApi.getHealthcareBurden(30),
      ]);
      setSignals((sRes.data ?? sRes ?? []) as OutbreakSignal[]);
      setBurden((bRes.data ?? bRes) as Record<string, unknown>);
    } catch (e) {
      console.error("Failed to load public health data", e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Public Health Intelligence</h1>
        <p className="text-sm text-gray-500 mt-1">Nationwide epidemiology, disease surveillance, and population health analytics</p>
      </div>

      {burden && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card">
            <p className="text-sm text-gray-500">Total Visits (30d)</p>
            <p className="text-2xl font-bold">{(burden as { total_visits: number }).total_visits?.toLocaleString() || "—"}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Diagnoses (30d)</p>
            <p className="text-2xl font-bold text-blue-600">{(burden as { total_diagnoses: number }).total_diagnoses?.toLocaleString() || "—"}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Patients Served</p>
            <p className="text-2xl font-bold text-green-600">{(burden as { patients_served: number }).patients_served?.toLocaleString() || "—"}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Visits/Day</p>
            <p className="text-2xl font-bold">{(burden as { visits_per_day: number }).visits_per_day || "—"}</p>
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Outbreak Early Warning Signals (14d)</h2>
        {signals.length === 0 ? (
          <p className="text-gray-500 text-sm">No outbreak signals detected</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b">
                  <th className="text-left px-3 py-2 text-gray-600 font-medium">Disease</th>
                  <th className="text-left px-3 py-2 text-gray-600 font-medium">ICD Code</th>
                  <th className="text-right px-3 py-2 text-gray-600 font-medium">Recent Cases</th>
                  <th className="text-right px-3 py-2 text-gray-600 font-medium">Baseline</th>
                  <th className="text-right px-3 py-2 text-gray-600 font-medium">Ratio</th>
                  <th className="text-left px-3 py-2 text-gray-600 font-medium">Signal</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {signals.map((s) => (
                  <tr key={s.icd_code} className={`hover:bg-gray-50 ${s.signal_strength === "high" ? "bg-red-50" : "bg-yellow-50"}`}>
                    <td className="px-3 py-2 font-medium text-gray-900">{s.diagnosis_name}</td>
                    <td className="px-3 py-2 text-gray-600">{s.icd_code}</td>
                    <td className="px-3 py-2 text-right font-medium">{s.recent_count}</td>
                    <td className="px-3 py-2 text-right text-gray-500">{s.baseline_count}</td>
                    <td className="px-3 py-2 text-right font-bold">{s.ratio}x</td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                        s.signal_strength === "high" ? "bg-red-200 text-red-800" : "bg-yellow-200 text-yellow-800"
                      }`}>
                        {s.signal_strength}
                      </span>
                    </td>
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
