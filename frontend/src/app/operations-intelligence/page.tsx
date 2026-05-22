"use client";

import { useEffect, useState } from "react";
import { operationsApi } from "@/lib/api/operations";
import { digitalTwinApi } from "@/lib/api/digitalTwin";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { OperationalAlert, DeviceTelemetryAnalytics } from "@/lib/types";

export default function OperationsIntelligencePage() {
  const [alerts, setAlerts] = useState<OperationalAlert[]>([]);
  const [loadData, setLoadData] = useState<Record<string, unknown> | null>(null);
  const [resourceData, setResourceData] = useState<Record<string, unknown> | null>(null);
  const [bottlenecks, setBottlenecks] = useState<Record<string, unknown>[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [threatIntel, setThreatIntel] = useState<Record<string, unknown> | null>(null);
  const [twins, setTwins] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"efficiency" | "alerts" | "security" | "twins">("efficiency");

  useEffect(() => {
    loadAll();
  }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [loadRes, resourceRes, bottleneckRes, recRes, alertRes, twinRes] = await Promise.all([
        operationsApi.hospitalLoad(),
        operationsApi.resourceAllocation(),
        operationsApi.bottlenecks(),
        operationsApi.recommendations(),
        operationsApi.listAlerts({ is_resolved: "false" }),
        digitalTwinApi.list({ is_active: "true" }),
      ]);
      if (loadRes.data) setLoadData(loadRes.data as unknown as Record<string, unknown>);
      if (resourceRes.data) setResourceData(resourceRes.data as unknown as Record<string, unknown>);
      setBottlenecks((bottleneckRes.results ?? bottleneckRes.data ?? []) as unknown as Record<string, unknown>[]);
      setRecommendations((recRes.results ?? recRes.data ?? []) as string[]);
      setAlerts((alertRes.results ?? alertRes.data ?? []) as OperationalAlert[]);
      setTwins((twinRes.results ?? twinRes.data ?? []) as unknown as Record<string, unknown>[]);
    } catch (e) {
      console.error("Failed to load operations data", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleThreatIntel() {
    try {
      const res = await operationsApi.threatIntel();
      if (res.data) setThreatIntel(res.data as unknown as Record<string, unknown>);
    } catch (e) {
      console.error("Failed to load threat intel", e);
    }
  }

  const tabs = [
    { key: "efficiency" as const, label: "Efficiency & Capacity" },
    { key: "alerts" as const, label: "Operational Alerts" },
    { key: "security" as const, label: "Security Intel" },
    { key: "twins" as const, label: "Digital Twins" },
  ];

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Operations Intelligence</h1>
        <p className="text-sm text-gray-500 mt-1">Hospital efficiency analysis, resource allocation, operational alerts, and security intelligence</p>
      </div>

      <div className="flex space-x-1 border-b border-gray-200">
        {tabs.map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === tab.key ? "border-primary-600 text-primary-700" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "efficiency" && (
        <div className="space-y-6">
          {loadData && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Hospital Efficiency Score</h2>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Overall Score</p>
                  <p className="text-2xl font-bold text-primary-600">{(loadData as { efficiency_score?: number }).efficiency_score ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Bed Occupancy</p>
                  <p className="text-lg font-bold">{(loadData as { bed_occupancy_pct?: number }).bed_occupancy_pct ?? "—"}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Staff Utilization</p>
                  <p className="text-lg font-bold">{(loadData as { staff_utilization_pct?: number }).staff_utilization_pct ?? "—"}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Available Beds</p>
                  <p className="text-lg font-bold text-green-600">{(loadData as { available_beds?: number }).available_beds ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Daily Admissions</p>
                  <p className="text-lg font-bold">{(loadData as { avg_daily_admissions?: number }).avg_daily_admissions ?? "—"}</p>
                </div>
              </div>
            </div>
          )}

          {resourceData && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Resource Allocation Forecast</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Projected Bed Need</p>
                  <p className="text-lg font-bold">{(resourceData as { projected_bed_need?: number }).projected_bed_need ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Projected Staff Need</p>
                  <p className="text-lg font-bold">{(resourceData as { projected_staff_need?: number }).projected_staff_need ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Risk Level</p>
                  <p className={`text-lg font-bold ${(resourceData as { risk_level?: string }).risk_level === "high" ? "text-red-600" : (resourceData as { risk_level?: string }).risk_level === "medium" ? "text-yellow-600" : "text-green-600"}`}>
                    {(resourceData as { risk_level?: string }).risk_level ?? "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Forecast Days</p>
                  <p className="text-lg font-bold">{(resourceData as { forecast_days?: number }).forecast_days ?? "—"}</p>
                </div>
              </div>
              {(resourceData as { projected_equipment_need?: Record<string, number> }).projected_equipment_need && (
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-2">Equipment Needs</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries((resourceData as { projected_equipment_need: Record<string, number> }).projected_equipment_need || {}).map(([key, val]) => (
                      <span key={key} className="px-2 py-1 text-xs bg-gray-100 rounded-full">{key}: {val}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {bottlenecks.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Operational Bottlenecks</h2>
              <div className="space-y-2">
                {bottlenecks.map((b, i) => (
                  <div key={i} className="border border-gray-200 rounded-lg p-3 text-sm">
                    <p className="font-medium text-gray-900">{(b as { area?: string }).area || (b as { department?: string }).department || `Bottleneck ${i + 1}`}</p>
                    <p className="text-gray-600 mt-0.5">{(b as { description?: string }).description || JSON.stringify(b)}</p>
                    {(b as { impact?: string }).impact && <p className="text-xs text-gray-500 mt-1">Impact: {(b as { impact: string }).impact}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {recommendations.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Optimization Recommendations</h2>
              <ul className="space-y-2">
                {recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start space-x-2 text-sm">
                    <span className="text-primary-600 mt-0.5">•</span>
                    <span className="text-gray-700">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {activeTab === "alerts" && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Operational Alerts ({alerts.length})</h2>
          {alerts.length === 0 ? (
            <p className="text-sm text-gray-500">No active alerts</p>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div key={alert.id} className={`border-l-4 p-4 rounded-r-lg ${
                  alert.severity === "critical" ? "border-red-400 bg-red-50" :
                  alert.severity === "high" ? "border-orange-400 bg-orange-50" :
                  alert.severity === "medium" ? "border-yellow-400 bg-yellow-50" :
                  "border-blue-400 bg-blue-50"
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                        alert.severity === "critical" ? "bg-red-200 text-red-800" :
                        alert.severity === "high" ? "bg-orange-200 text-orange-800" :
                        alert.severity === "medium" ? "bg-yellow-200 text-yellow-800" :
                        "bg-blue-200 text-blue-800"
                      }`}>{alert.severity}</span>
                      <span className="text-xs text-gray-400">{alert.category}</span>
                    </div>
                    <span className="text-xs text-gray-400">{new Date(alert.created_at).toLocaleString()}</span>
                  </div>
                  <h3 className="font-semibold text-gray-900 mt-1">{alert.title}</h3>
                  <p className="text-sm text-gray-600">{alert.description}</p>
                  {alert.metric_name && (
                    <p className="text-xs text-gray-500 mt-1">Metric: {alert.metric_name} {alert.metric_value !== null ? `= ${alert.metric_value}` : ""}</p>
                  )}
                  {alert.recommended_action && (
                    <p className="text-xs text-primary-600 mt-1">Recommended: {alert.recommended_action}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">Source: {alert.source_service}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "security" && (
        <div className="space-y-4">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Threat Intelligence</h2>
            {!threatIntel ? (
              <button onClick={handleThreatIntel} className="btn btn-primary">Load Threat Intelligence</button>
            ) : (
              <pre className="text-sm text-gray-600 bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
                {JSON.stringify(threatIntel, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}

      {activeTab === "twins" && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Infrastructure Digital Twins ({twins.length})</h2>
          {twins.length === 0 ? (
            <p className="text-sm text-gray-500">No digital twins configured</p>
          ) : (
            <div className="space-y-3">
              {twins.map((twin) => (
                <div key={(twin as { id: number }).id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{(twin as { name: string }).name}</h3>
                      <p className="text-sm text-gray-500">{(twin as { twin_type: string }).twin_type?.replace(/_/g, " ")} — {(twin as { region: string }).region}</p>
                      <span className={`inline-block px-2 py-0.5 text-xs rounded-full mt-1 ${
                        (twin as { simulation_status: string }).simulation_status === "completed" ? "bg-green-100 text-green-700" :
                        (twin as { simulation_status: string }).simulation_status === "running" ? "bg-yellow-100 text-yellow-700" :
                        "bg-gray-100 text-gray-600"
                      }`}>
                        {(twin as { simulation_status: string }).simulation_status}
                      </span>
                    </div>
                    {(twin as { last_simulated_at: string | null }).last_simulated_at && (
                      <span className="text-xs text-gray-400">Last simulated: {new Date((twin as { last_simulated_at: string }).last_simulated_at).toLocaleDateString()}</span>
                    )}
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
