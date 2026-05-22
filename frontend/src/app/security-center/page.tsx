"use client";

import { useEffect, useState } from "react";
import { securityApi } from "@/lib/api/security";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { SecurityEvent, DeviceFingerprint, RiskDashboard } from "@/lib/types";

type Tab = "events" | "devices" | "mfa" | "dashboard";

export default function SecurityCenterPage() {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [dashboard, setDashboard] = useState<RiskDashboard | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [devices, setDevices] = useState<DeviceFingerprint[]>([]);
  const [mfaSecret, setMfaSecret] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  async function loadData() {
    setLoading(true);
    try {
      if (activeTab === "dashboard") {
        const res = await securityApi.getRiskDashboard();
        setDashboard((res.data ?? res) as RiskDashboard);
      }
      if (activeTab === "events") {
        const res = await securityApi.listEvents();
        setEvents((res.results ?? res.data ?? []) as SecurityEvent[]);
      }
      if (activeTab === "devices") {
        const res = await securityApi.listDevices();
        setDevices((res.results ?? res.data ?? []) as DeviceFingerprint[]);
      }
    } catch (e) {
      console.error("Failed to load security data", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleResolve(id: number) {
    await securityApi.resolveEvent(id);
    loadData();
  }

  async function handleMfaSetup() {
    const res = await securityApi.setupMfa();
    setMfaSecret((res.data as { secret: string }).secret ?? "");
  }

  async function handleMfaVerify() {
    const res = await securityApi.verifyMfa(mfaCode);
    if (res.success) setMfaEnabled(true);
  }

  async function handleMfaDisable() {
    await securityApi.disableMfa();
    setMfaEnabled(false);
    setMfaSecret("");
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "dashboard", label: "Risk Dashboard" },
    { key: "events", label: "Security Events" },
    { key: "devices", label: "Devices" },
    { key: "mfa", label: "MFA Settings" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Security Center</h1>
        <p className="text-sm text-gray-500 mt-1">Zero-trust security monitoring and management</p>
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
          {activeTab === "dashboard" && dashboard && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="card border-l-4 border-red-500">
                  <p className="text-sm text-gray-500">High Risk Events</p>
                  <p className="text-2xl font-bold text-red-600">{dashboard.total_high_risk}</p>
                </div>
                <div className="card border-l-4 border-orange-500">
                  <p className="text-sm text-gray-500">Critical (24h)</p>
                  <p className="text-2xl font-bold text-orange-600">{dashboard.critical_events_24h}</p>
                </div>
                <div className="card border-l-4 border-yellow-500">
                  <p className="text-sm text-gray-500">Flagged Users</p>
                  <p className="text-2xl font-bold text-yellow-600">{dashboard.unique_users_flagged}</p>
                </div>
              </div>

              {dashboard.recent_unresolved.length > 0 && (
                <div className="card">
                  <h2 className="text-lg font-semibold mb-4">Unresolved Critical Events</h2>
                  <div className="space-y-3">
                    {dashboard.recent_unresolved.map((ev) => (
                      <div key={ev.id} className="flex items-start justify-between p-3 bg-red-50 rounded-lg">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                              ev.severity === "critical" ? "bg-red-200 text-red-800" : "bg-orange-200 text-orange-800"
                            }`}>
                              {ev.severity}
                            </span>
                            <span className="text-sm font-medium text-gray-900">{ev.category.replace(/_/g, " ")}</span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{ev.description}</p>
                          <p className="text-xs text-gray-400 mt-1">Score: {ev.risk_score} | {new Date(ev.detected_at).toLocaleString()}</p>
                        </div>
                        <button onClick={() => handleResolve(ev.id)} className="btn btn-sm btn-secondary">Resolve</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "events" && (
            <div className="card">
              {events.length === 0 ? (
                <p className="text-gray-500 text-sm">No security events</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b">
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Severity</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Category</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Description</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Score</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Time</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Resolved</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {events.map((ev) => (
                        <tr key={ev.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2">
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                              ev.severity === "critical" ? "bg-red-200 text-red-800" :
                              ev.severity === "high" ? "bg-orange-200 text-orange-800" :
                              ev.severity === "medium" ? "bg-yellow-200 text-yellow-800" :
                              "bg-gray-200 text-gray-800"
                            }`}>{ev.severity}</span>
                          </td>
                          <td className="px-3 py-2 text-gray-900">{ev.category.replace(/_/g, " ")}</td>
                          <td className="px-3 py-2 text-gray-600 max-w-xs truncate">{ev.description}</td>
                          <td className="px-3 py-2 text-right">{ev.risk_score.toFixed(2)}</td>
                          <td className="px-3 py-2 text-right text-gray-500">{new Date(ev.detected_at).toLocaleString()}</td>
                          <td className="px-3 py-2 text-right">{ev.resolved ? "Yes" : "No"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === "devices" && (
            <div className="card">
              {devices.length === 0 ? (
                <p className="text-gray-500 text-sm">No registered devices</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b">
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Device</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">OS</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Browser</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Risk Count</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Trusted</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Last Seen</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {devices.map((d) => (
                        <tr key={d.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2 font-medium text-gray-900">{d.device_name || "Unknown"}</td>
                          <td className="px-3 py-2 text-gray-600">{d.os || "-"}</td>
                          <td className="px-3 py-2 text-gray-600">{d.browser || "-"}</td>
                          <td className="px-3 py-2 text-right">{d.risk_count}</td>
                          <td className="px-3 py-2 text-right">{d.is_trusted ? "Yes" : "No"}</td>
                          <td className="px-3 py-2 text-right text-gray-500">{new Date(d.last_seen_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === "mfa" && (
            <div className="card max-w-lg">
              <h2 className="text-lg font-semibold mb-4">Multi-Factor Authentication</h2>
              {!mfaSecret && !mfaEnabled ? (
                <div>
                  <p className="text-sm text-gray-600 mb-4">Enable MFA to add an extra layer of security to your account.</p>
                  <button onClick={handleMfaSetup} className="btn btn-primary">Enable MFA</button>
                </div>
              ) : mfaSecret && !mfaEnabled ? (
                <div className="space-y-4">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500 mb-1">Your MFA Secret</p>
                    <p className="text-sm font-mono bg-white p-2 rounded border">{mfaSecret}</p>
                  </div>
                  <p className="text-sm text-gray-600">Enter the 6-digit code from your authenticator app:</p>
                  <div className="flex space-x-2">
                    <input value={mfaCode} onChange={(e) => setMfaCode(e.target.value)} placeholder="000000" className="input flex-1 font-mono text-center" maxLength={6} />
                    <button onClick={handleMfaVerify} className="btn btn-primary">Verify</button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                    <span className="text-sm font-medium text-green-700">MFA is active</span>
                  </div>
                  <button onClick={handleMfaDisable} className="btn btn-sm btn-secondary">Disable</button>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
