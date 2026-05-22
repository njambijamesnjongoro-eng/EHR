"use client";

import { useEffect, useState } from "react";
import { smartHospitalAutomationApi } from "@/lib/api/smartHospitalAutomation";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { SmartDeviceEvent, HospitalIoTSummary, PatientFlowAnalysis, Bottleneck, PredictiveStaffing } from "@/lib/types";

export default function SmartHospitalOpsPage() {
  const [events, setEvents] = useState<SmartDeviceEvent[]>([]);
  const [iotSummary, setIotSummary] = useState<HospitalIoTSummary | null>(null);
  const [patientFlow, setPatientFlow] = useState<PatientFlowAnalysis | null>(null);
  const [bottlenecks, setBottlenecks] = useState<Bottleneck[]>([]);
  const [staffing, setStaffing] = useState<PredictiveStaffing | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"events" | "bottlenecks" | "staffing">("events");

  useEffect(() => {
    loadAll();
  }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [eventsRes, iotRes, flowRes, bottleRes, staffRes] = await Promise.all([
        smartHospitalAutomationApi.listDeviceEvents(),
        smartHospitalAutomationApi.iotSummary(),
        smartHospitalAutomationApi.patientFlow(),
        smartHospitalAutomationApi.bottlenecks(),
        smartHospitalAutomationApi.staffing(),
      ]);
      setEvents((eventsRes.results ?? eventsRes.data ?? []) as SmartDeviceEvent[]);
      if (iotRes.data) setIotSummary(iotRes.data);
      if (flowRes.data) setPatientFlow(flowRes.data);
      setBottlenecks((bottleRes.results ?? bottleRes.data ?? []) as Bottleneck[]);
      if (staffRes.data) setStaffing(staffRes.data);
    } catch (e) {
      console.error("Failed to load smart hospital data", e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  const tabs = [
    { key: "events" as const, label: "Device Events" },
    { key: "bottlenecks" as const, label: "Bottlenecks" },
    { key: "staffing" as const, label: "Staffing" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Smart Hospital Operations</h1>
        <p className="text-sm text-gray-500 mt-1">IoT device monitoring, patient flow, and operational automation</p>
      </div>

      {iotSummary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="card text-center"><p className="text-xs text-gray-500">Total Devices</p><p className="text-xl font-bold">{iotSummary.total_devices}</p></div>
          <div className="card text-center"><p className="text-xs text-gray-500">Online</p><p className="text-xl font-bold text-green-600">{iotSummary.online}</p></div>
          <div className="card text-center"><p className="text-xs text-gray-500">Offline</p><p className="text-xl font-bold text-red-600">{iotSummary.offline}</p></div>
          <div className="card text-center"><p className="text-xs text-gray-500">Events/hr</p><p className="text-xl font-bold">{iotSummary.events_last_hour}</p></div>
          <div className="card text-center"><p className="text-xs text-gray-500">Critical/hr</p><p className="text-xl font-bold text-red-600">{iotSummary.critical_events_last_hour}</p></div>
          <div className="card text-center"><p className="text-xs text-gray-500">Uptime</p><p className="text-xl font-bold">{iotSummary.uptime_pct}%</p></div>
        </div>
      )}

      {patientFlow && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Patient Flow Analysis</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div><p className="text-xs text-gray-500">Avg Daily Admissions</p><p className="font-semibold text-lg">{patientFlow.avg_daily_admissions}</p></div>
            <div><p className="text-xs text-gray-500">Avg Daily Discharges</p><p className="font-semibold text-lg">{patientFlow.avg_daily_discharges}</p></div>
            <div><p className="text-xs text-gray-500">Peak Hour</p><p className="font-semibold text-lg">{patientFlow.peak_activity_hour ?? "N/A"}:00</p></div>
            <div><p className="text-xs text-gray-500">Admission Trend</p><p className="font-semibold text-lg capitalize">{patientFlow.admission_trend}</p></div>
          </div>
        </div>
      )}

      <div className="flex space-x-1 border-b border-gray-200">
        {tabs.map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === tab.key ? "border-primary-600 text-primary-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "events" && (
        <div className="space-y-3">
          {events.length === 0 ? (
            <div className="card"><p className="text-gray-500 text-sm">No device events recorded</p></div>
          ) : (
            events.map((ev) => {
              const severityColors: Record<string, string> = {
                info: "bg-blue-100 text-blue-800",
                warning: "bg-yellow-100 text-yellow-800",
                critical: "bg-orange-100 text-orange-800",
                emergency: "bg-red-100 text-red-800",
              };
              return (
                <div key={ev.id} className="card">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${severityColors[ev.severity] || "bg-gray-100"}`}>
                          {ev.severity.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-500">{ev.event_category.replace(/_/g, " ")}</span>
                        <span className="text-xs text-gray-400">{ev.device_name}</span>
                      </div>
                      <p className="text-sm font-medium text-gray-900">{ev.event_type}</p>
                      {ev.value !== null && <p className="text-xs text-gray-600">{ev.value} {ev.unit}</p>}
                      <p className="text-xs text-gray-400 mt-1">Ward: {ev.ward_name}</p>
                    </div>
                    <div className="ml-4 text-right">
                      <p className="text-xs text-gray-400">{new Date(ev.occurred_at).toLocaleString()}</p>
                      {ev.is_processed && <span className="text-xs text-green-600">Processed</span>}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {activeTab === "bottlenecks" && (
        <div className="space-y-3">
          {bottlenecks.length === 0 ? (
            <div className="card"><p className="text-gray-500 text-sm">No bottlenecks detected</p></div>
          ) : (
            bottlenecks.map((b, i) => {
              const sevColors: Record<string, string> = {
                low: "bg-yellow-50 border-yellow-200",
                medium: "bg-orange-50 border-orange-200",
                high: "bg-red-50 border-red-200",
                critical: "bg-red-100 border-red-300",
              };
              return (
                <div key={i} className={`card border-l-4 ${sevColors[b.severity] || "bg-gray-50 border-gray-200"}`}>
                  <div className="flex justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{b.ward_name}</h3>
                      <p className="text-sm text-gray-600">{b.type}</p>
                      <p className="text-xs text-gray-500 mt-1">{b.recommendation}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold">{b.utilization_pct}%</p>
                      <p className="text-xs text-gray-500 capitalize">{b.severity}</p>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {activeTab === "staffing" && staffing && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Predictive Staffing</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div><p className="text-xs text-gray-500">Avg Daily Admissions</p><p className="font-semibold text-lg">{staffing.avg_daily_admissions}</p></div>
            <div><p className="text-xs text-gray-500">Current Occupancy</p><p className="font-semibold text-lg">{staffing.current_occupancy}</p></div>
            <div><p className="text-xs text-gray-500">Total Beds</p><p className="font-semibold text-lg">{staffing.total_beds}</p></div>
            <div><p className="text-xs text-gray-500">Projected Occupancy</p><p className="font-semibold text-lg">{staffing.projected_occupancy}</p></div>
            <div><p className="text-xs text-gray-500">Forecast Days</p><p className="font-semibold text-lg">{staffing.forecast_days}</p></div>
            <div><p className="text-xs text-gray-500">Recommended Staff Ratio</p><p className="font-semibold text-lg text-primary-600">{staffing.recommended_staff_ratio}</p></div>
          </div>
        </div>
      )}
    </div>
  );
}
