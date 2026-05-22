"use client";

import { useEffect, useState } from "react";
import { complianceApi } from "@/lib/api/compliance";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { ConsentLog, EnterpriseAuditEvent, AuditReport } from "@/lib/types";

type Tab = "consents" | "audit" | "report";

export default function CompliancePage() {
  const [activeTab, setActiveTab] = useState<Tab>("consents");
  const [consents, setConsents] = useState<ConsentLog[]>([]);
  const [auditEvents, setAuditEvents] = useState<EnterpriseAuditEvent[]>([]);
  const [report, setReport] = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  async function loadData() {
    setLoading(true);
    try {
      if (activeTab === "consents") {
        const res = await complianceApi.listConsents();
        setConsents((res.results ?? res.data ?? []) as ConsentLog[]);
      }
      if (activeTab === "audit") {
        const res = await complianceApi.listAuditEvents();
        setAuditEvents((res.results ?? res.data ?? []) as EnterpriseAuditEvent[]);
      }
      if (activeTab === "report") {
        const res = await complianceApi.getAuditReport(30);
        setReport((res.data ?? res) as AuditReport);
      }
    } catch (e) {
      console.error("Failed to load compliance data", e);
    } finally {
      setLoading(false);
    }
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "consents", label: "Patient Consents" },
    { key: "audit", label: "Audit Trail" },
    { key: "report", label: "Audit Report" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance & Governance</h1>
        <p className="text-sm text-gray-500 mt-1">Consent management, audit trail, and governance reporting</p>
      </div>

      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === t.key ? "bg-white text-primary-700 shadow-sm" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? <LoadingSpinner /> : (
        <>
          {activeTab === "consents" && (
            <div className="card">
              {consents.length === 0 ? (
                <p className="text-gray-500 text-sm">No consent records found</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b">
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Patient</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Type</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Status</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Granted By</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Granted At</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Expires</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {consents.map((c) => (
                        <tr key={c.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2 font-medium text-gray-900">{c.patient_name}</td>
                          <td className="px-3 py-2">{c.consent_type.replace(/_/g, " ")}</td>
                          <td className="px-3 py-2">
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                              c.status === "granted" ? "bg-green-200 text-green-800" :
                              c.status === "revoked" ? "bg-red-200 text-red-800" :
                              "bg-gray-200 text-gray-800"
                            }`}>{c.status}</span>
                          </td>
                          <td className="px-3 py-2 text-gray-600">{c.granted_by_name}</td>
                          <td className="px-3 py-2 text-right text-gray-500">{new Date(c.granted_at).toLocaleDateString()}</td>
                          <td className="px-3 py-2 text-right text-gray-500">{c.expires_at ? new Date(c.expires_at).toLocaleDateString() : "Never"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === "audit" && (
            <div className="card">
              {auditEvents.length === 0 ? (
                <p className="text-gray-500 text-sm">No audit events</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b">
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Type</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Action</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Resource</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">User</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Severity</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {auditEvents.map((ev) => (
                        <tr key={ev.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2 font-medium text-gray-900">{ev.event_type.replace(/_/g, " ")}</td>
                          <td className="px-3 py-2">{ev.action}</td>
                          <td className="px-3 py-2 text-gray-600">{ev.resource_type}#{ev.resource_id}</td>
                          <td className="px-3 py-2 text-gray-600">{ev.user_name || "System"}</td>
                          <td className="px-3 py-2">
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                              ev.severity === "critical" ? "bg-red-200 text-red-800" :
                              ev.severity === "error" ? "bg-orange-200 text-orange-800" :
                              ev.severity === "warning" ? "bg-yellow-200 text-yellow-800" :
                              "bg-gray-200 text-gray-800"
                            }`}>{ev.severity}</span>
                          </td>
                          <td className="px-3 py-2 text-right text-gray-500">{new Date(ev.created_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === "report" && report && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="card">
                  <p className="text-sm text-gray-500">Total Events</p>
                  <p className="text-2xl font-bold">{report.total_events.toLocaleString()}</p>
                </div>
                <div className="card">
                  <p className="text-sm text-gray-500">Security Events</p>
                  <p className="text-2xl font-bold text-red-600">{report.security_events}</p>
                </div>
                <div className="card">
                  <p className="text-sm text-gray-500">Unique Users</p>
                  <p className="text-2xl font-bold">{Object.keys(report.by_user).length}</p>
                </div>
                <div className="card">
                  <p className="text-sm text-gray-500">Period</p>
                  <p className="text-2xl font-bold">{report.period_days} days</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">By Event Type</h3>
                  <div className="space-y-2">
                    {Object.entries(report.by_event_type).map(([key, val]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-gray-600">{key.replace(/_/g, " ")}</span>
                        <span className="font-medium">{val}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">By Severity</h3>
                  <div className="space-y-2">
                    {Object.entries(report.by_severity).map(([key, val]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-gray-600 capitalize">{key}</span>
                        <span className="font-medium">{val}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="card">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Top Users</h3>
                <div className="space-y-2">
                  {Object.entries(report.by_user).slice(0, 10).map(([email, count]) => (
                    <div key={email} className="flex justify-between text-sm">
                      <span className="text-gray-600">{email}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
