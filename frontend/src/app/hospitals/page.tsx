"use client";

import { useEffect, useState } from "react";
import { hospitalApi } from "@/lib/api/hospitals";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { Hospital, Department, HospitalStaff } from "@/lib/types";

export default function HospitalsPage() {
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<number | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [staff, setStaff] = useState<HospitalStaff[]>([]);

  useEffect(() => {
    loadHospitals();
  }, []);

  useEffect(() => {
    if (selected) loadDetails(selected);
  }, [selected]);

  async function loadHospitals() {
    try {
      const res = await hospitalApi.list();
      setHospitals((res.data ?? []) as Hospital[]);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function loadDetails(id: number) {
    try {
      const [dRes, sRes] = await Promise.all([
        hospitalApi.listDepartments(id),
        hospitalApi.listStaff(id),
      ]);
      setDepartments((dRes.data ?? []) as Department[]);
      setStaff((sRes.data ?? []) as HospitalStaff[]);
    } catch (e) {
      console.error(e);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Hospital Management</h1>
        <p className="text-sm text-gray-500 mt-1">Manage hospitals, departments, and staff across the national network</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-2">
          {hospitals.map((h) => (
            <button
              key={h.id}
              onClick={() => setSelected(h.id)}
              className={`w-full text-left p-4 rounded-xl border transition-colors ${
                selected === h.id
                  ? "border-primary-500 bg-primary-50"
                  : "border-gray-200 hover:bg-gray-50"
              }`}
            >
              <p className="font-semibold text-gray-900">{h.hospital_name}</p>
              <p className="text-sm text-gray-500">{h.hospital_code} · {h.county}</p>
              <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full ${
                h.is_active ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
              }`}>
                {h.is_active ? "Active" : "Inactive"}
              </span>
            </button>
          ))}
        </div>

        <div className="lg:col-span-2">
          {selected ? (
            <div className="space-y-6">
              <div className="card">
                <h2 className="text-lg font-semibold mb-4">Departments</h2>
                {departments.length === 0 ? (
                  <p className="text-gray-500 text-sm">No departments</p>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {departments.map((d) => (
                      <div key={d.id} className="p-3 bg-gray-50 rounded-lg">
                        <p className="font-medium text-sm">{d.department_name}</p>
                        <p className="text-xs text-gray-400">{d.department_code}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="card">
                <h2 className="text-lg font-semibold mb-4">Staff</h2>
                {staff.length === 0 ? (
                  <p className="text-gray-500 text-sm">No staff assigned</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50 border-b">
                          <th className="text-left px-3 py-2 text-gray-600 font-medium">Name</th>
                          <th className="text-left px-3 py-2 text-gray-600 font-medium">Role</th>
                          <th className="text-left px-3 py-2 text-gray-600 font-medium">Department</th>
                          <th className="text-left px-3 py-2 text-gray-600 font-medium">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {staff.map((s) => (
                          <tr key={s.id} className="hover:bg-gray-50">
                            <td className="px-3 py-2 font-medium">{s.user_name || s.user_email}</td>
                            <td className="px-3 py-2 capitalize">{s.staff_role.replace("_", " ")}</td>
                            <td className="px-3 py-2 text-gray-500">{s.department_name || "—"}</td>
                            <td className="px-3 py-2">
                              <span className={`text-xs px-2 py-0.5 rounded-full ${s.is_active ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
                                {s.is_active ? "Active" : "Inactive"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card text-center py-12">
              <p className="text-gray-500">Select a hospital to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
