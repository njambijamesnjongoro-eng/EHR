"use client";

import { useEffect, useState } from "react";
import { monitoringApi } from "@/lib/api/monitoring";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { SystemHealthDashboard } from "@/lib/types";

export default function MonitoringPage() {
  const [dashboard, setDashboard] = useState<SystemHealthDashboard | null>(null);
  const [health, setHealth] = useState<{ status: string; checks: Record<string, unknown> } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
      const [dRes, hRes] = await Promise.all([
        monitoringApi.getDashboard(),
        monitoringApi.getHealth(),
      ]);
      setDashboard((dRes.data ?? dRes) as SystemHealthDashboard);
      setHealth(hRes as { status: string; checks: Record<string, unknown> });
    } catch (e) {
      console.error("Failed to load monitoring data", e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
        <p className="text-sm text-gray-500 mt-1">Real-time system health and performance metrics</p>
      </div>

      {health && (
        <div className={`card border-l-4 ${health.status === "healthy" ? "border-green-500" : "border-red-500"}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${health.status === "healthy" ? "bg-green-500" : "bg-red-500"}`} />
              <span className="font-semibold text-lg capitalize">{health.status}</span>
            </div>
            <span className="text-sm text-gray-500">System Status</span>
          </div>
        </div>
      )}

      {health?.checks && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(health.checks as Record<string, { status: string }>).map(([key, val]) => (
            <div key={key} className="card">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{key.replace(/_/g, " ")}</p>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${val.status === "healthy" ? "bg-green-500" : "bg-yellow-500"}`} />
                <span className="text-sm font-medium capitalize">{val.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {dashboard && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card">
              <p className="text-sm text-gray-500">Queue Depth</p>
              <p className="text-2xl font-bold text-gray-900">{dashboard.queue_depth}</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Active Users</p>
              <p className="text-2xl font-bold text-blue-600">{dashboard.active_users}</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Cache Hit Ratio</p>
              <p className="text-2xl font-bold text-green-600">{(dashboard.cache_hit_ratio * 100).toFixed(1)}%</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Error Rate (24h)</p>
              <p className="text-2xl font-bold text-red-600">{(dashboard.error_rate_24h * 100).toFixed(2)}%</p>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Recent Metrics</h2>
            {dashboard.recent_metrics.length === 0 ? (
              <p className="text-gray-500 text-sm">No metrics recorded yet</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b">
                      <th className="text-left px-3 py-2 text-gray-600 font-medium">Metric</th>
                      <th className="text-right px-3 py-2 text-gray-600 font-medium">Value</th>
                      <th className="text-right px-3 py-2 text-gray-600 font-medium">Unit</th>
                      <th className="text-right px-3 py-2 text-gray-600 font-medium">Time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {dashboard.recent_metrics.slice(0, 30).map((m) => (
                      <tr key={m.id} className="hover:bg-gray-50">
                        <td className="px-3 py-2 font-medium">{m.metric_type.replace(/_/g, " ")}</td>
                        <td className="px-3 py-2 text-right">{m.value}</td>
                        <td className="px-3 py-2 text-right text-gray-500">{m.unit}</td>
                        <td className="px-3 py-2 text-right text-gray-500">{new Date(m.recorded_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
