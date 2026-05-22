"use client";

import { useEffect, useState } from "react";
import { precisionHealthApi } from "@/lib/api/precisionHealth";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { HealthRiskProfile, PatientRiskSummary } from "@/lib/types";

export default function PrecisionHealthPage() {
  const [profiles, setProfiles] = useState<HealthRiskProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [patientId, setPatientId] = useState("");
  const [riskCategory, setRiskCategory] = useState("general");
  const [assessing, setAssessing] = useState(false);
  const [riskSummary, setRiskSummary] = useState<PatientRiskSummary | null>(null);
  const [querySummary, setQuerySummary] = useState("");
  const [activeTab, setActiveTab] = useState<"profiles" | "high-risk" | "assess">("profiles");

  useEffect(() => {
    loadProfiles();
  }, []);

  async function loadProfiles() {
    setLoading(true);
    try {
      const res = await precisionHealthApi.listProfiles();
      setProfiles((res.results ?? res.data ?? []) as HealthRiskProfile[]);
    } catch (e) {
      console.error("Failed to load risk profiles", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleAssessRisk() {
    if (!patientId) return;
    setAssessing(true);
    try {
      const res = await precisionHealthApi.assessRisk(Number(patientId), riskCategory);
      if (res.data) setProfiles((prev) => [res.data as HealthRiskProfile, ...prev]);
    } catch (e) {
      console.error("Failed to assess risk", e);
    } finally {
      setAssessing(false);
    }
  }

  async function handleLoadSummary() {
    if (!querySummary) return;
    try {
      const res = await precisionHealthApi.patientRiskSummary(Number(querySummary));
      if (res.data) setRiskSummary(res.data);
    } catch (e) {
      console.error("Failed to load risk summary", e);
    }
  }

  async function loadHighRisk() {
    setActiveTab("high-risk");
    setLoading(true);
    try {
      const res = await precisionHealthApi.highRisk();
      setProfiles((res.results ?? res.data ?? []) as HealthRiskProfile[]);
    } catch (e) {
      console.error("Failed to load high risk profiles", e);
    } finally {
      setLoading(false);
    }
  }

  const riskLevelColors: Record<string, string> = {
    low: "bg-green-100 text-green-800",
    moderate: "bg-yellow-100 text-yellow-800",
    high: "bg-orange-100 text-orange-800",
    critical: "bg-red-100 text-red-800",
  };

  const tabs = [
    { key: "profiles" as const, label: "All Profiles" },
    { key: "high-risk" as const, label: "High Risk" },
    { key: "assess" as const, label: "Risk Assessment" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Precision Health</h1>
        <p className="text-sm text-gray-500 mt-1">AI-driven health risk profiling and predictive analytics</p>
      </div>

      <div className="flex space-x-1 border-b border-gray-200">
        {tabs.map((tab) => (
          <button key={tab.key} onClick={() => {
            setActiveTab(tab.key);
            if (tab.key === "high-risk") loadHighRisk();
            if (tab.key === "profiles") loadProfiles();
          }} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === tab.key ? "border-primary-600 text-primary-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "assess" && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Assess Patient Risk</h2>
          <div className="flex items-end space-x-3">
            <div className="flex-1">
              <label className="label">Patient ID</label>
              <input type="number" value={patientId} onChange={(e) => setPatientId(e.target.value)} className="input" placeholder="Enter patient ID" />
            </div>
            <div>
              <label className="label">Risk Category</label>
              <select value={riskCategory} onChange={(e) => setRiskCategory(e.target.value)} className="input">
                <option value="general">General</option>
                <option value="cardiovascular">Cardiovascular</option>
                <option value="diabetes">Diabetes</option>
                <option value="respiratory">Respiratory</option>
                <option value="cancer">Cancer</option>
                <option value="mental_health">Mental Health</option>
                <option value="fall">Fall Risk</option>
                <option value="readmission">Readmission</option>
              </select>
            </div>
            <button onClick={handleAssessRisk} disabled={!patientId || assessing} className="btn btn-primary">
              {assessing ? "Assessing..." : "Assess Risk"}
            </button>
          </div>
        </div>
      )}

      {activeTab === "profiles" && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Risk Profiles</h2>
            <div className="flex items-center space-x-2">
              <input value={querySummary} onChange={(e) => setQuerySummary(e.target.value)} className="input w-40" placeholder="Patient ID" />
              <button onClick={handleLoadSummary} className="btn btn-secondary text-sm">Summary</button>
            </div>
          </div>
          {riskSummary && (
            <div className="mb-4 p-3 bg-blue-50 rounded-lg">
              <p className="font-semibold text-sm">Patient #{riskSummary.patient_id} - Overall: {riskSummary.overall_risk}</p>
              {riskSummary.profiles.map((p, i) => (
                <p key={i} className="text-xs text-gray-600">{p.category}: {p.score} ({p.level})</p>
              ))}
            </div>
          )}
          {loading ? <LoadingSpinner /> : profiles.length === 0 ? (
            <p className="text-gray-500 text-sm">No risk profiles found</p>
          ) : (
            <div className="space-y-3">
              {profiles.map((p) => (
                <div key={p.id} className="p-3 border border-gray-200 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{p.patient_name}</p>
                      <p className="text-sm text-gray-500">{p.risk_category_display}</p>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${riskLevelColors[p.risk_level] || "bg-gray-100"}`}>
                        {p.risk_level.toUpperCase()} {p.risk_score}
                      </span>
                    </div>
                  </div>
                  {p.contributing_factors.length > 0 && (
                    <details className="mt-2">
                      <summary className="text-xs text-primary-600 cursor-pointer">Contributing Factors</summary>
                      <ul className="mt-1 space-y-1">
                        {p.contributing_factors.map((f, i) => (
                          <li key={i} className="text-xs text-gray-500">- {f}</li>
                        ))}
                      </ul>
                    </details>
                  )}
                  <p className="text-xs text-gray-400 mt-2">Last assessed: {new Date(p.last_assessed_at).toLocaleString()}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "high-risk" && (
        <div>
          {loading ? <LoadingSpinner /> : profiles.length === 0 ? (
            <div className="card"><p className="text-gray-500 text-sm">No high-risk patients found</p></div>
          ) : (
            <div className="space-y-3">
              {profiles.map((p) => (
                <div key={p.id} className="card border-red-200 bg-red-50">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-semibold text-gray-900">{p.patient_name}</p>
                      <p className="text-sm text-gray-600">{p.risk_category_display}</p>
                      {p.contributing_factors.slice(0, 3).map((f, i) => (
                        <p key={i} className="text-xs text-gray-500">- {f}</p>
                      ))}
                    </div>
                    <div className="text-right">
                      <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-red-200 text-red-800">
                        {p.risk_level.toUpperCase()} {p.risk_score}
                      </span>
                      {p.longitudinal_trend.length > 0 && (
                        <p className="text-xs text-gray-500 mt-1">Trend: [{p.longitudinal_trend.slice(-5).join(", ")}]</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
