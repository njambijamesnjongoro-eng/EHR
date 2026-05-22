"use client";

import { useEffect, useState } from "react";
import { wearableApi } from "@/lib/api/wearable";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { WearableDevice, DeviceReading } from "@/lib/types";

export default function WearablePage() {
  const [devices, setDevices] = useState<WearableDevice[]>([]);
  const [readings, setReadings] = useState<DeviceReading[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"devices" | "readings">("devices");

  useEffect(() => {
    loadData();
  }, [tab]);

  async function loadData() {
    setLoading(true);
    try {
      if (tab === "devices") {
        const res = await wearableApi.listDevices();
        setDevices((res.results ?? res.data ?? []) as WearableDevice[]);
      } else {
        const res = await wearableApi.listReadings();
        setReadings((res.results ?? res.data ?? []) as DeviceReading[]);
      }
    } catch (e) {
      console.error("Failed to load wearable data", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Wearable & IoT Devices</h1>
        <p className="text-sm text-gray-500 mt-1">Patient wearable device management and real-time monitoring</p>
      </div>

      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-64">
        <button onClick={() => setTab("devices")} className={`flex-1 px-4 py-2 text-sm font-medium rounded-md ${tab === "devices" ? "bg-white shadow-sm" : "text-gray-600"}`}>Devices</button>
        <button onClick={() => setTab("readings")} className={`flex-1 px-4 py-2 text-sm font-medium rounded-md ${tab === "readings" ? "bg-white shadow-sm" : "text-gray-600"}`}>Readings</button>
      </div>

      {loading ? <LoadingSpinner /> : (
        <>
          {tab === "devices" && (
            <div className="card">
              {devices.length === 0 ? (
                <p className="text-gray-500 text-sm">No wearable devices registered</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b">
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Device</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Type</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Patient</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Status</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Verified</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Last Sync</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {devices.map((d) => (
                        <tr key={d.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2 font-medium text-gray-900">{d.device_name}</td>
                          <td className="px-3 py-2 text-gray-600">{d.device_type.replace(/_/g, " ")}</td>
                          <td className="px-3 py-2 text-gray-600">{d.patient}</td>
                          <td className="px-3 py-2">
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${d.is_active ? "bg-green-200 text-green-800" : "bg-gray-200 text-gray-800"}`}>
                              {d.is_active ? "Active" : "Inactive"}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-right">{d.is_verified ? "Yes" : "No"}</td>
                          <td className="px-3 py-2 text-right text-gray-500">{d.last_sync_at ? new Date(d.last_sync_at).toLocaleString() : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {tab === "readings" && (
            <div className="card">
              {readings.length === 0 ? (
                <p className="text-gray-500 text-sm">No device readings recorded</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b">
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Type</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Value</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Unit</th>
                        <th className="text-left px-3 py-2 text-gray-600 font-medium">Status</th>
                        <th className="text-right px-3 py-2 text-gray-600 font-medium">Recorded At</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {readings.slice(0, 100).map((r) => (
                        <tr key={r.id} className={`hover:bg-gray-50 ${r.is_abnormal ? "bg-red-50" : ""}`}>
                          <td className="px-3 py-2 font-medium text-gray-900">{r.reading_type.replace(/_/g, " ")}</td>
                          <td className="px-3 py-2 text-right font-mono">{r.value}</td>
                          <td className="px-3 py-2 text-gray-600">{r.unit}</td>
                          <td className="px-3 py-2">
                            {r.is_abnormal && <span className="text-xs font-medium text-red-600">ABNORMAL</span>}
                          </td>
                          <td className="px-3 py-2 text-right text-gray-500">{new Date(r.recorded_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
