"use client";

import { useEffect, useState } from "react";
import { reportsApi } from "@/lib/api/reports";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { DashboardStats } from "@/lib/types";

export default function OperationsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    try {
      const res = await reportsApi.getDashboardStats();
      const data: DashboardStats = res.data ?? (res as unknown as DashboardStats);
      setStats(data);
    } catch (e) {
      console.error("Failed to load dashboard stats", e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner />;
  if (!stats) return <div className="card text-center py-12"><p className="text-gray-500">Failed to load operations data</p></div>;

  const bedPct = stats.total_beds > 0 ? Math.round((stats.occupied_beds / stats.total_beds) * 100) : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Operations Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Hospital-wide operational metrics and oversight</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Active Admissions" value={stats.active_admissions} icon="🏥" color="blue" />
        <StatCard title="Bed Occupancy" value={`${bedPct}%`} subtitle={`${stats.occupied_beds}/${stats.total_beds} beds`} icon="🛏️" color={bedPct >= 90 ? "red" : bedPct >= 60 ? "yellow" : "green"} />
        <StatCard title="Today's Visits" value={stats.today_visits} icon="👨‍⚕️" color="purple" />
        <StatCard title="Monthly Revenue" value={`KES ${(stats.monthly_revenue || 0).toLocaleString()}`} icon="💰" color="green" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Pending Actions</h2>
          <div className="space-y-4">
            <PendingItem label="Pending Lab Requests" value={stats.pending_labs} href="#" color="yellow" />
            <PendingItem label="Pending Imaging" value={stats.pending_imaging} href="/imaging" color="blue" />
            <PendingItem label="Pending Invoices" value={stats.pending_invoices} href="/billing" color="red" />
            <PendingItem label="Total Patients" value={stats.total_patients} href="/patients/search" color="green" />
            <PendingItem label="Total Visits (All Time)" value={stats.total_visits} href="#" color="gray" />
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Ward Occupancy</h2>
          <div className="space-y-4">
            {(stats.ward_stats || []).map((ward) => {
              const pct = ward.total_beds > 0 ? Math.round((ward.occ_beds / ward.total_beds) * 100) : 0;
              const color = pct >= 90 ? "bg-red-500" : pct >= 60 ? "bg-yellow-500" : "bg-green-500";
              return (
                <div key={ward.ward_name}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-gray-700">{ward.ward_name}</span>
                    <span className="text-gray-500">{ward.occ_beds}/{ward.total_beds}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${Math.min(pct, 100)}%` }} />
                  </div>
                </div>
              );
            })}
            {(!stats.ward_stats || stats.ward_stats.length === 0) && (
              <p className="text-gray-500 text-sm">No ward data available</p>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <QuickActionButton label="Admit Patient" href="/admissions" color="blue" />
          <QuickActionButton label="New Invoice" href="/billing" color="green" />
          <QuickActionButton label="Imaging Request" href="/imaging" color="purple" />
          <QuickActionButton label="Register Patient" href="/patients/register" color="orange" />
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, subtitle, icon, color }: {
  title: string; value: string | number; subtitle?: string; icon: string; color: string;
}) {
  const colorMap: Record<string, string> = {
    blue: "bg-blue-50 text-blue-700",
    green: "bg-green-50 text-green-700",
    red: "bg-red-50 text-red-700",
    yellow: "bg-yellow-50 text-yellow-700",
    purple: "bg-purple-50 text-purple-700",
    gray: "bg-gray-50 text-gray-700",
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span className={`text-xs font-medium px-2 py-1 rounded ${colorMap[color] || colorMap.blue}`}>
          {title.split(" ")[0]}
        </span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{subtitle || title}</p>
    </div>
  );
}

function PendingItem({ label, value, href, color }: {
  label: string; value: number; href: string; color: string;
}) {
  const colorMap: Record<string, string> = {
    red: "text-red-600",
    yellow: "text-yellow-600",
    blue: "text-blue-600",
    green: "text-green-600",
    gray: "text-gray-600",
  };

  return (
    <a href={href} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors">
      <span className="text-sm text-gray-700">{label}</span>
      <span className={`text-lg font-bold ${colorMap[color]}`}>{value}</span>
    </a>
  );
}

function QuickActionButton({ label, href, color }: {
  label: string; href: string; color: string;
}) {
  const colorMap: Record<string, string> = {
    blue: "bg-blue-50 text-blue-700 hover:bg-blue-100",
    green: "bg-green-50 text-green-700 hover:bg-green-100",
    purple: "bg-purple-50 text-purple-700 hover:bg-purple-100",
    orange: "bg-orange-50 text-orange-700 hover:bg-orange-100",
  };

  return (
    <a
      href={href}
      className={`text-center p-4 rounded-xl font-medium text-sm transition-colors ${colorMap[color]}`}
    >
      {label}
    </a>
  );
}
