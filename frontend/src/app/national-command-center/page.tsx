"use client";

import { useEffect, useState } from "react";
import { digitalTwinApi } from "@/lib/api/digitalTwin";
import { emergencyResponseApi } from "@/lib/api/emergencyResponse";
import { populationHealthApi } from "@/lib/api/populationHealth";
import { operationsApi } from "@/lib/api/operations";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { InfrastructureTwin, NationalEmergencyOverview, PopulationHealthInsight, OperationalAlert } from "@/lib/types";

export default function NationalCommandCenterPage() {
  const [twins, setTwins] = useState<InfrastructureTwin[]>([]);
  const [overview, setOverview] = useState<NationalEmergencyOverview | null>(null);
  const [insights, setInsights] = useState<PopulationHealthInsight[]>([]);
  const [alerts, setAlerts] = useState<OperationalAlert[]>([]);
  const [loadData, setLoadData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAll();
  }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [twinRes, overviewRes, insightRes, alertRes, loadRes] = await Promise.all([
        digitalTwinApi.list({ is_active: "true" }),
        emergencyResponseApi.nationalOverview(),
        populationHealthApi.listInsights({ limit: 5 }),
        operationsApi.listAlerts({ is_resolved: "false", limit: 10 }),
        operationsApi.hospitalLoad(),
      ]);
      setTwins((twinRes.results ?? twinRes.data ?? []) as InfrastructureTwin[]);
      if (overviewRes.data) setOverview(overviewRes.data);
      setInsights((insightRes.results ?? insightRes.data ?? []) as PopulationHealthInsight[]);
      setAlerts((alertRes.results ?? alertRes.data ?? []) as OperationalAlert[]);
      if (loadRes.data) setLoadData(loadRes.data as unknown as Record<string, unknown>);
    } catch (e) {
      console.error("Failed to load command center data", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleSimulate(id: number) {
    try {
      await digitalTwinApi.runSimulation(id);
      loadAll();
    } catch (e) {
      console.error("Failed to run simulation", e);
    }
  }

  const severityColors: Record<string, string> = {
    level_1: "bg-green-100 text-green-800",
    level_2: "bg-yellow-100 text-yellow-800",
    level_3: "bg-orange-100 text-orange-800",
    level_4: "bg-red-100 text-red-800",
    level_5: "bg-purple-100 text-purple-800",
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">National Command Center</h1>
        <p className="text-sm text-gray-500 mt-1">Centralized national healthcare situational awareness, digital twins, and operational intelligence</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Active Emergencies</p>
          <p className="text-2xl font-bold text-red-600">{overview?.total_active || 0}</p>
          {overview && overview.total_active > 0 && (
            <div className="mt-1 text-xs text-gray-500">
              {Object.entries(overview.by_severity || {}).map(([sev, count]) => (
                <span key={sev} className={`inline-block px-1.5 py-0.5 rounded mr-1 ${severityColors[sev] || "bg-gray-100"}`}>{sev.replace("level_", "L")}: {count}</span>
              ))}
            </div>
          )}
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Active Twins</p>
          <p className="text-2xl font-bold text-blue-600">{twins.filter(t => t.is_active).length}</p>
          <p className="text-xs text-gray-400 mt-1">{twins.filter(t => t.simulation_status === "completed").length} completed simulations</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Population Insights</p>
          <p className="text-2xl font-bold text-green-600">{insights.length}</p>
          <p className="text-xs text-gray-400 mt-1">Latest health indicators</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Active Alerts</p>
          <p className="text-2xl font-bold text-orange-600">{alerts.length}</p>
          <p className="text-xs text-gray-400 mt-1">Requiring attention</p>
        </div>
      </div>

      {loadData && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Hospital Load Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-500">Bed Occupancy</p>
              <p className="text-lg font-bold">{(loadData as { bed_occupancy_pct?: number }).bed_occupancy_pct ?? "—"}%</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Available Beds</p>
              <p className="text-lg font-bold text-green-600">{(loadData as { available_beds?: number }).available_beds ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Daily Admissions</p>
              <p className="text-lg font-bold">{(loadData as { avg_daily_admissions?: number }).avg_daily_admissions ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Efficiency Score</p>
              <p className="text-lg font-bold text-blue-600">{(loadData as { efficiency_score?: number }).efficiency_score ?? "—"}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Infrastructure Digital Twins</h2>
          {twins.length === 0 ? (
            <p className="text-sm text-gray-500">No active twins configured</p>
          ) : (
            <div className="space-y-3">
              {twins.map((twin) => (
                <div key={twin.id} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{twin.name}</h3>
                      <p className="text-xs text-gray-500">{twin.twin_type.replace(/_/g, " ")} — {twin.region}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className={`px-1.5 py-0.5 text-xs rounded-full ${twin.simulation_status === "completed" ? "bg-green-100 text-green-700" : twin.simulation_status === "running" ? "bg-yellow-100 text-yellow-700" : "bg-gray-100 text-gray-600"}`}>
                          {twin.simulation_status}
                        </span>
                        {twin.last_simulated_at && (
                          <span className="text-xs text-gray-400">Last: {new Date(twin.last_simulated_at).toLocaleString()}</span>
                        )}
                      </div>
                    </div>
                    <button onClick={() => handleSimulate(twin.id)} className="px-3 py-1 text-xs font-medium bg-primary-100 text-primary-700 rounded hover:bg-primary-200">
                      Simulate
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Operational Alerts</h2>
          {alerts.length === 0 ? (
            <p className="text-sm text-gray-500">No active alerts</p>
          ) : (
            <div className="space-y-2">
              {alerts.slice(0, 8).map((alert) => (
                <div key={alert.id} className={`border-l-4 p-3 rounded-r-lg text-sm ${
                  alert.severity === "critical" ? "border-red-400 bg-red-50" :
                  alert.severity === "high" ? "border-orange-400 bg-orange-50" :
                  alert.severity === "medium" ? "border-yellow-400 bg-yellow-50" :
                  "border-blue-400 bg-blue-50"
                }`}>
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-gray-900">{alert.title}</p>
                    <span className={`px-1.5 py-0.5 text-xs rounded-full ${
                      alert.severity === "critical" ? "bg-red-200 text-red-800" :
                      alert.severity === "high" ? "bg-orange-200 text-orange-800" :
                      alert.severity === "medium" ? "bg-yellow-200 text-yellow-800" :
                      "bg-blue-200 text-blue-800"
                    }`}>{alert.severity}</span>
                  </div>
                  <p className="text-gray-600 mt-0.5">{alert.description}</p>
                  {alert.recommended_action && (
                    <p className="text-xs text-gray-500 mt-1">Action: {alert.recommended_action}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Population Health Highlights</h2>
        {insights.length === 0 ? (
          <p className="text-sm text-gray-500">No population health data available</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left text-gray-500">
                  <th className="pb-2 pr-4 font-medium">Indicator</th>
                  <th className="pb-2 pr-4 font-medium">County</th>
                  <th className="pb-2 pr-4 font-medium">Value</th>
                  <th className="pb-2 pr-4 font-medium">Population</th>
                  <th className="pb-2 pr-4 font-medium">Trend</th>
                  <th className="pb-2 pr-4 font-medium">Period</th>
                </tr>
              </thead>
              <tbody>
                {insights.map((insight) => (
                  <tr key={insight.id} className="border-b border-gray-100">
                    <td className="py-2 pr-4 font-medium text-gray-900">{insight.indicator_name}</td>
                    <td className="py-2 pr-4 text-gray-600">{insight.county}</td>
                    <td className="py-2 pr-4">{insight.indicator_value?.toLocaleString()}</td>
                    <td className="py-2 pr-4 text-gray-600">{insight.population_base?.toLocaleString()}</td>
                    <td className="py-2 pr-4">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        insight.trend_direction === "up" ? "bg-red-100 text-red-700" :
                        insight.trend_direction === "down" ? "bg-green-100 text-green-700" :
                        "bg-gray-100 text-gray-600"
                      }`}>{insight.trend_direction}</span>
                    </td>
                    <td className="py-2 pr-4 text-gray-500">{new Date(insight.period_start).toLocaleDateString()} — {new Date(insight.period_end).toLocaleDateString()}</td>
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
