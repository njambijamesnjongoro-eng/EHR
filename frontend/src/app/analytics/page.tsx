"use client";

import { useEffect, useState } from "react";
import { analyticsApi } from "@/lib/api/analytics";
import { useAuth } from "@/lib/auth-context";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { HospitalDashboardData, RevenueMonthly, NationalAggregate } from "@/lib/types";

export default function AnalyticsPage() {
  const { user } = useAuth();
  const isNational = user?.role === "super_admin";

  const [dashboard, setDashboard] = useState<HospitalDashboardData | null>(null);
  const [revenue, setRevenue] = useState<RevenueMonthly[]>([]);
  const [national, setNational] = useState<NationalAggregate | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    loadData();
  }, [days]);

  async function loadData() {
    setLoading(true);
    try {
      const [dRes, rRes] = await Promise.all([
        analyticsApi.getDashboard(days),
        analyticsApi.getRevenue(12),
      ]);
      setDashboard((dRes.data ?? dRes) as HospitalDashboardData);
      setRevenue((rRes.data?.monthly ?? []) as RevenueMonthly[]);

      if (isNational) {
        const nRes = await analyticsApi.getNationalAggregate();
        setNational((nRes.data ?? nRes) as NationalAggregate);
      }
    } catch (e) {
      console.error("Failed to load analytics", e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics & Reports</h1>
          <p className="text-sm text-gray-500 mt-1">Hospital performance metrics and insights</p>
        </div>
        <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="input w-40">
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      {dashboard && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card">
              <p className="text-sm text-gray-500">Total Patients</p>
              <p className="text-2xl font-bold text-gray-900">{dashboard.total_patients.toLocaleString()}</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Visits ({days}d)</p>
              <p className="text-2xl font-bold text-blue-600">{dashboard.total_visits}</p>
              <p className="text-xs text-gray-400">{dashboard.daily_avg_visits}/day avg</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Revenue ({days}d)</p>
              <p className="text-2xl font-bold text-green-600">KES {dashboard.total_revenue.toLocaleString()}</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Collected</p>
              <p className="text-2xl font-bold text-green-600">KES {dashboard.total_collected.toLocaleString()}</p>
              <p className="text-xs text-gray-400">Outstanding: KES {dashboard.outstanding.toLocaleString()}</p>
            </div>
          </div>

          {dashboard.top_diagnoses && dashboard.top_diagnoses.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Top Diagnoses ({days}d)</h2>
              <div className="space-y-3">
                {dashboard.top_diagnoses.map((d, i) => (
                  <div key={d.diagnosis_name} className="flex items-center">
                    <span className="text-sm text-gray-400 w-6">{i + 1}.</span>
                    <span className="flex-1 text-sm font-medium text-gray-900">{d.diagnosis_name}</span>
                    <span className="text-sm text-gray-500">{d.count} cases</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Monthly Revenue</h2>
            {revenue.length === 0 ? (
              <p className="text-gray-500 text-sm">No revenue data</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b">
                      <th className="text-left px-3 py-2 text-gray-600 font-medium">Month</th>
                      <th className="text-right px-3 py-2 text-gray-600 font-medium">Invoices</th>
                      <th className="text-right px-3 py-2 text-gray-600 font-medium">Total</th>
                      <th className="text-right px-3 py-2 text-gray-600 font-medium">Collected</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {revenue.map((r) => (
                      <tr key={r.month} className="hover:bg-gray-50">
                        <td className="px-3 py-2 font-medium">{r.month}</td>
                        <td className="px-3 py-2 text-right">{r.count}</td>
                        <td className="px-3 py-2 text-right">KES {r.total.toLocaleString()}</td>
                        <td className="px-3 py-2 text-right text-green-600">KES {r.collected.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {national && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">National Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <p className="text-sm text-gray-500">Total Hospitals</p>
              <p className="text-xl font-bold">{national.total_hospitals}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Patients</p>
              <p className="text-xl font-bold">{national.total_patients.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Visits</p>
              <p className="text-xl font-bold">{national.total_visits.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Referrals</p>
              <p className="text-xl font-bold">{national.total_referrals}</p>
            </div>
          </div>
          {national.hospitals_by_county.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Hospitals by County</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {national.hospitals_by_county.map((h) => (
                  <div key={h.county} className="flex justify-between text-sm p-2 bg-gray-50 rounded">
                    <span>{h.county}</span>
                    <span className="font-medium">{h.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
