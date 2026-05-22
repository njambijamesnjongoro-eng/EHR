"use client";

import { useEffect, useState } from "react";
import { emergencyResponseApi } from "@/lib/api/emergencyResponse";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { EmergencyResponseEvent, NationalEmergencyOverview, RegionalCapacity } from "@/lib/types";

export default function EmergencyResponsePage() {
  const [events, setEvents] = useState<EmergencyResponseEvent[]>([]);
  const [activeEvents, setActiveEvents] = useState<EmergencyResponseEvent[]>([]);
  const [nationalOverview, setNationalOverview] = useState<NationalEmergencyOverview | null>(null);
  const [regionalCapacity, setRegionalCapacity] = useState<RegionalCapacity | null>(null);
  const [region, setRegion] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [listRes, activeRes, overviewRes] = await Promise.all([
        emergencyResponseApi.list(),
        emergencyResponseApi.activeEmergencies(),
        emergencyResponseApi.nationalOverview(),
      ]);
      setEvents((listRes.results ?? listRes.data ?? []) as EmergencyResponseEvent[]);
      setActiveEvents((activeRes.results ?? activeRes.data ?? []) as EmergencyResponseEvent[]);
      if (overviewRes.data) setNationalOverview(overviewRes.data);
    } catch (e) {
      console.error("Failed to load emergency data", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleRegionalCapacity() {
    if (!region) return;
    try {
      const res = await emergencyResponseApi.regionalCapacity(region);
      if (res.data) setRegionalCapacity(res.data);
    } catch (e) {
      console.error("Failed to load regional capacity", e);
    }
  }

  async function handleUpdateStatus(id: number, status: string) {
    try {
      await emergencyResponseApi.updateStatus(id, status);
      loadData();
    } catch (e) {
      console.error("Failed to update status", e);
    }
  }

  const severityColors: Record<string, string> = {
    level_1: "bg-green-100 text-green-800",
    level_2: "bg-yellow-100 text-yellow-800",
    level_3: "bg-orange-100 text-orange-800",
    level_4: "bg-red-100 text-red-800",
    level_5: "bg-purple-100 text-purple-800",
  };

  const statusColors: Record<string, string> = {
    active: "bg-red-200 text-red-800",
    responding: "bg-yellow-200 text-yellow-800",
    contained: "bg-blue-200 text-blue-800",
    resolved: "bg-green-200 text-green-800",
    aftermath: "bg-gray-200 text-gray-800",
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Emergency Response Coordination</h1>
        <p className="text-sm text-gray-500 mt-1">Nationwide emergency management, regional capacity, and incident response</p>
      </div>

      {nationalOverview && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="card">
            <p className="text-sm text-gray-500">Active Emergencies</p>
            <p className="text-2xl font-bold text-red-600">{nationalOverview.total_active}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Affected Regions</p>
            <p className="text-2xl font-bold">{nationalOverview.affected_regions.length}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Affected Population</p>
            <p className="text-2xl font-bold">{nationalOverview.total_affected_population?.toLocaleString() || "—"}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Hospitals Impacted</p>
            <p className="text-2xl font-bold text-orange-600">{nationalOverview.hospitals_impacted}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">By Severity</p>
            <div className="text-sm font-medium space-y-1 mt-1">
              {Object.entries(nationalOverview.by_severity || {}).map(([sev, count]) => (
                <span key={sev} className={`inline-block px-2 py-0.5 rounded-full text-xs mr-1 ${severityColors[sev] || "bg-gray-100"}`}>
                  {sev.replace("level_", "L")}: {count}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Emergencies ({activeEvents.length})</h2>
          {activeEvents.length === 0 ? (
            <p className="text-sm text-gray-500">No active emergencies</p>
          ) : (
            <div className="space-y-3">
              {activeEvents.map((ev) => (
                <div key={ev.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${severityColors[ev.severity] || "bg-gray-100"}`}>
                          {ev.severity.replace("_", " ").toUpperCase()}
                        </span>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusColors[ev.status] || "bg-gray-100"}`}>
                          {ev.status.replace("_", " ").toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-400">{ev.emergency_type.replace(/_/g, " ")}</span>
                      </div>
                      <h3 className="font-semibold text-gray-900">{ev.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{ev.description}</p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>Region: {ev.location_region}</span>
                        <span>Casualties: {ev.estimated_casualties?.toLocaleString() || 0}</span>
                        <span>Population: {ev.affected_population?.toLocaleString() || 0}</span>
                      </div>
                    </div>
                    <div className="ml-4 flex flex-col space-y-2">
                      {ev.status === "active" && (
                        <button onClick={() => handleUpdateStatus(ev.id, "responding")} className="px-3 py-1 text-xs font-medium bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200">
                          Respond
                        </button>
                      )}
                      {ev.status === "responding" && (
                        <button onClick={() => handleUpdateStatus(ev.id, "contained")} className="px-3 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
                          Contain
                        </button>
                      )}
                      {ev.status === "contained" && (
                        <button onClick={() => handleUpdateStatus(ev.id, "resolved")} className="px-3 py-1 text-xs font-medium bg-green-100 text-green-700 rounded hover:bg-green-200">
                          Resolve
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Regional Capacity</h2>
            <div className="flex items-center space-x-2 mb-3">
              <input type="text" value={region} onChange={(e) => setRegion(e.target.value)} className="input flex-1" placeholder="Enter region" />
              <button onClick={handleRegionalCapacity} className="btn btn-primary btn-sm">Lookup</button>
            </div>
            {regionalCapacity && (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Total Hospitals</span><span className="font-medium">{regionalCapacity.total_hospitals}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Total Beds</span><span className="font-medium">{regionalCapacity.total_beds}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Available Beds</span><span className="font-medium text-green-600">{regionalCapacity.available_beds}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">ICU Beds</span><span className="font-medium">{regionalCapacity.icu_beds}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Available ICU</span><span className="font-medium text-green-600">{regionalCapacity.available_icu}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">ER Available</span><span className="font-medium">{regionalCapacity.emergency_rooms_available}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Staffing</span><span className={`font-medium ${regionalCapacity.staffing_level === "critical" ? "text-red-600" : regionalCapacity.staffing_level === "low" ? "text-yellow-600" : "text-green-600"}`}>{regionalCapacity.staffing_level}</span></div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">All Emergency Events ({events.length})</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500">
                <th className="pb-2 pr-4 font-medium">Title</th>
                <th className="pb-2 pr-4 font-medium">Type</th>
                <th className="pb-2 pr-4 font-medium">Severity</th>
                <th className="pb-2 pr-4 font-medium">Status</th>
                <th className="pb-2 pr-4 font-medium">Region</th>
                <th className="pb-2 pr-4 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.id} className="border-b border-gray-100">
                  <td className="py-2 pr-4 font-medium text-gray-900">{ev.title}</td>
                  <td className="py-2 pr-4 text-gray-600 capitalize">{ev.emergency_type.replace(/_/g, " ")}</td>
                  <td className="py-2 pr-4"><span className={`px-2 py-0.5 text-xs font-medium rounded-full ${severityColors[ev.severity] || "bg-gray-100"}`}>{ev.severity.replace("_", " ").toUpperCase()}</span></td>
                  <td className="py-2 pr-4"><span className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusColors[ev.status] || "bg-gray-100"}`}>{ev.status.replace("_", " ").toUpperCase()}</span></td>
                  <td className="py-2 pr-4 text-gray-600">{ev.location_region}</td>
                  <td className="py-2 pr-4 text-gray-500">{new Date(ev.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
