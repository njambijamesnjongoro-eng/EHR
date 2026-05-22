"use client";

import { useEffect, useState } from "react";
import { citizenSuperPortalApi } from "@/lib/api/citizenSuperPortal";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { CitizenFullHealthRecord, EmergencyProfile, CareReminder } from "@/lib/types";

export default function CitizenSuperPortalPage() {
  const [healthRecord, setHealthRecord] = useState<CitizenFullHealthRecord | null>(null);
  const [emergencyProfile, setEmergencyProfile] = useState<EmergencyProfile | null>(null);
  const [reminders, setReminders] = useState<CareReminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"record" | "emergency" | "share" | "reminders">("record");
  const [shareEmail, setShareEmail] = useState("");
  const [shareDataTypes, setShareDataTypes] = useState("lab_results,diagnoses,medications");
  const [shareResult, setShareResult] = useState<{ share_token: string; expires_at: string } | null>(null);
  const [sharing, setSharing] = useState(false);

  useEffect(() => {
    loadAll();
  }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [recordRes, emergencyRes, remindersRes] = await Promise.all([
        citizenSuperPortalApi.fullHealthRecord(),
        citizenSuperPortalApi.emergencyProfile(),
        citizenSuperPortalApi.careReminders(),
      ]);
      if (recordRes.data) setHealthRecord(recordRes.data);
      if (emergencyRes.data) setEmergencyProfile(emergencyRes.data);
      setReminders((remindersRes.results ?? remindersRes.data ?? []) as CareReminder[]);
    } catch (e) {
      console.error("Failed to load citizen portal data", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleShare() {
    if (!shareEmail) return;
    setSharing(true);
    try {
      const res = await citizenSuperPortalApi.shareData(shareEmail, shareDataTypes.split(",").map((s) => s.trim()), 24);
      if (res.data) setShareResult(res.data);
    } catch (e) {
      console.error("Failed to share data", e);
    } finally {
      setSharing(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  const tabs = [
    { key: "record" as const, label: "Health Record" },
    { key: "emergency" as const, label: "Emergency Profile" },
    { key: "share" as const, label: "Share Data" },
    { key: "reminders" as const, label: "Reminders" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Citizen Super Portal</h1>
        <p className="text-sm text-gray-500 mt-1">Complete health record, emergency profile, and secure data sharing</p>
      </div>

      <div className="flex space-x-1 border-b border-gray-200">
        {tabs.map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === tab.key ? "border-primary-600 text-primary-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "record" && healthRecord && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-3">Personal Information</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div><p className="text-xs text-gray-500">Name</p><p className="font-medium">{healthRecord.patient.full_name}</p></div>
              <div><p className="text-xs text-gray-500">Health ID</p><p className="font-medium">{healthRecord.patient.health_id}</p></div>
              <div><p className="text-xs text-gray-500">Gender</p><p className="font-medium capitalize">{healthRecord.patient.gender}</p></div>
              <div><p className="text-xs text-gray-500">Blood Group</p><p className="font-medium">{healthRecord.patient.blood_group}</p></div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="text-lg font-semibold mb-3">Recent Visits</h2>
              {healthRecord.recent_visits.length === 0 ? (
                <p className="text-sm text-gray-500">No recent visits</p>
              ) : (
                <div className="space-y-2">
                  {healthRecord.recent_visits.slice(0, 5).map((v) => (
                    <div key={v.id} className="p-2 bg-gray-50 rounded">
                      <p className="text-sm font-medium">{v.date}</p>
                      <p className="text-xs text-gray-600">{v.complaint}</p>
                      <p className="text-xs text-gray-400">Dr. {v.doctor}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <h2 className="text-lg font-semibold mb-3">Active Prescriptions</h2>
              {healthRecord.active_prescriptions.length === 0 ? (
                <p className="text-sm text-gray-500">No active prescriptions</p>
              ) : (
                <div className="space-y-2">
                  {healthRecord.active_prescriptions.map((p, i) => (
                    <div key={i} className="p-2 bg-blue-50 rounded">
                      <p className="text-sm font-medium">{p.medication}</p>
                      <p className="text-xs text-gray-600">{p.dosage} - {p.frequency}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold mb-3">Diagnoses</h2>
            {healthRecord.diagnoses.length === 0 ? (
              <p className="text-sm text-gray-500">No diagnoses recorded</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b">
                      <th className="text-left px-3 py-2 text-gray-600 font-medium">Diagnosis</th>
                      <th className="text-left px-3 py-2 text-gray-600 font-medium">ICD</th>
                      <th className="text-left px-3 py-2 text-gray-600 font-medium">Severity</th>
                      <th className="text-right px-3 py-2 text-gray-600 font-medium">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {healthRecord.diagnoses.map((d, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-3 py-2 font-medium">{d.name}</td>
                        <td className="px-3 py-2 text-gray-600">{d.icd}</td>
                        <td className="px-3 py-2 capitalize">{d.severity}</td>
                        <td className="px-3 py-2 text-right text-gray-500">{d.date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="text-lg font-semibold mb-3">Lab Results</h2>
              {healthRecord.lab_results.length === 0 ? (
                <p className="text-sm text-gray-500">No lab results</p>
              ) : (
                <div className="space-y-2">
                  {healthRecord.lab_results.map((l, i) => (
                    <div key={i} className={`p-2 rounded ${l.abnormal ? "bg-red-50" : "bg-gray-50"}`}>
                      <p className="text-sm font-medium">{l.test}</p>
                      <p className="text-xs text-gray-600">{l.result}</p>
                      <p className="text-xs text-gray-400">{l.date ?? "N/A"}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <h2 className="text-lg font-semibold mb-3">AI Insights & Recommendations</h2>
              {healthRecord.ai_insights.length === 0 && healthRecord.ai_recommendations.length === 0 ? (
                <p className="text-sm text-gray-500">No AI-generated insights</p>
              ) : (
                <div className="space-y-2">
                  {healthRecord.ai_insights.slice(0, 3).map((i) => (
                    <div key={i.id} className="p-2 bg-purple-50 rounded">
                      <p className="text-sm font-medium">{i.title}</p>
                      <p className="text-xs text-gray-500">{i.type} - {i.confidence}</p>
                    </div>
                  ))}
                  {healthRecord.ai_recommendations.slice(0, 3).map((r) => (
                    <div key={r.id} className="p-2 bg-indigo-50 rounded">
                      <p className="text-sm font-medium">{r.title}</p>
                      <p className="text-xs text-gray-500">{r.type} - {r.priority}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === "emergency" && emergencyProfile && (
        <div className="space-y-4">
          <div className="card">
            <h2 className="text-lg font-semibold mb-3">Emergency Contact Information</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div><p className="text-xs text-gray-500">Name</p><p className="font-medium">{emergencyProfile.patient.full_name}</p></div>
              <div><p className="text-xs text-gray-500">Health ID</p><p className="font-medium">{emergencyProfile.patient.health_id}</p></div>
              <div><p className="text-xs text-gray-500">Blood Group</p><p className="font-medium">{emergencyProfile.patient.blood_group}</p></div>
            </div>
          </div>
          <div className="card">
            <h2 className="text-lg font-semibold mb-3">Medical Profile</h2>
            <div className="space-y-2">
              <div><p className="text-xs text-gray-500">Allergies</p><p className="text-sm">{emergencyProfile.emergency.allergies || "None recorded"}</p></div>
              <div><p className="text-xs text-gray-500">Chronic Conditions</p><p className="text-sm">{emergencyProfile.emergency.chronic_conditions || "None"}</p></div>
              <div><p className="text-xs text-gray-500">Medications</p><p className="text-sm">{emergencyProfile.emergency.medications || "None"}</p></div>
            </div>
          </div>
          <div className="card">
            <h2 className="text-lg font-semibold mb-3">Active Prescriptions</h2>
            {emergencyProfile.active_prescriptions.length === 0 ? (
              <p className="text-sm text-gray-500">No active prescriptions</p>
            ) : (
              <div className="space-y-2">
                {emergencyProfile.active_prescriptions.map((p, i) => (
                  <div key={i} className="p-2 bg-blue-50 rounded">
                    <p className="text-sm font-medium">{p.medication_name}</p>
                    <p className="text-xs text-gray-600">{p.dosage} - {p.frequency}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "share" && (
        <div className="space-y-4">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Securely Share Your Health Data</h2>
            <div className="space-y-4">
              <div>
                <label className="label">Recipient Email</label>
                <input type="email" value={shareEmail} onChange={(e) => setShareEmail(e.target.value)} className="input" placeholder="doctor@example.com" />
              </div>
              <div>
                <label className="label">Data Types (comma-separated)</label>
                <input value={shareDataTypes} onChange={(e) => setShareDataTypes(e.target.value)} className="input" placeholder="lab_results,diagnoses,medications" />
              </div>
              <button onClick={handleShare} disabled={!shareEmail || sharing} className="btn btn-primary">
                {sharing ? "Sharing..." : "Share Data Securely"}
              </button>
            </div>
          </div>
          {shareResult && (
            <div className="card bg-green-50 border-green-200">
              <h3 className="font-semibold text-green-800">Data Shared Successfully</h3>
              <p className="text-sm text-green-700 mt-1">Share Token: <code className="bg-green-100 px-2 py-0.5 rounded">{shareResult.share_token}</code></p>
              <p className="text-xs text-green-600 mt-1">Expires: {new Date(shareResult.expires_at).toLocaleString()}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === "reminders" && (
        <div className="space-y-3">
          {reminders.length === 0 ? (
            <div className="card"><p className="text-gray-500 text-sm">No care reminders</p></div>
          ) : (
            reminders.map((r, i) => {
              const priorityColors: Record<string, string> = {
                low: "border-gray-200",
                medium: "border-yellow-200 bg-yellow-50",
                high: "border-orange-200 bg-orange-50",
                urgent: "border-red-200 bg-red-50",
              };
              return (
                <div key={i} className={`card border-l-4 ${priorityColors[r.priority] || "border-gray-200"}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900 capitalize">{r.type.replace(/_/g, " ")}</p>
                      <p className="text-sm text-gray-600">{r.message}</p>
                    </div>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${
                      r.priority === "high" || r.priority === "urgent" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-700"
                    }`}>
                      {r.priority}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
