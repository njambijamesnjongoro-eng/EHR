"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { patientApi } from "@/lib/api/patients";
import { clinicalApi } from "@/lib/api/clinical";
import { labApi } from "@/lib/api/labs";
import Sidebar from "@/components/layout/sidebar";
import Navbar from "@/components/layout/navbar";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { Patient, Visit, LabRequest } from "@/lib/types";

const quickActions = [
  {
    label: "Register Patient",
    href: "/patients/register",
    description: "Add a new patient record",
    color: "bg-blue-50 text-blue-700 border-blue-200",
    roles: ["super_admin", "hospital_admin", "doctor", "nurse", "receptionist"],
  },
  {
    label: "Search Patients",
    href: "/patients/search",
    description: "Find patient records and start visits",
    color: "bg-green-50 text-green-700 border-green-200",
    roles: ["super_admin", "hospital_admin", "doctor", "nurse", "lab_technician", "pharmacist", "receptionist"],
  },
];

export default function DashboardPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [recentPatients, setRecentPatients] = useState<Patient[]>([]);
  const [activeVisits, setActiveVisits] = useState<Visit[]>([]);
  const [pendingLabs, setPendingLabs] = useState<LabRequest[]>([]);
  const [isLoadingPatients, setIsLoadingPatients] = useState(true);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated) return;

    const isDoctor = user?.role === "doctor" || user?.role === "super_admin" || user?.role === "hospital_admin";

    Promise.all([
      patientApi.list({ page_size: 5, ordering: "-created_at" }),
      isDoctor ? clinicalApi.listVisits({ status: "in_progress" }) : Promise.resolve({ results: [] } as any),
      isDoctor ? labApi.listRequests({ status: "requested" }) : Promise.resolve({ results: [] } as any),
    ])
      .then(([patients, visits, labs]) => {
        setRecentPatients((patients.results || []) as unknown as Patient[]);
        setActiveVisits((visits.results || []) as unknown as Visit[]);
        setPendingLabs((labs.results || []) as unknown as LabRequest[]);
      })
      .catch(() => {})
      .finally(() => setIsLoadingPatients(false));
  }, [isAuthenticated, user?.role]);

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const allowedActions = quickActions.filter((a) => a.roles.includes(user.role));
  const isDoctor = user.role === "doctor" || user.role === "super_admin" || user.role === "hospital_admin";

  return (
    <div className="min-h-screen flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col">
        <Navbar onMenuToggle={() => setSidebarOpen(true)} />
        <main className="flex-1 p-6 bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-gray-900">
                Welcome, {user.first_name}
              </h1>
              <p className="text-gray-500 mt-1">
                {new Date().toLocaleDateString("en-US", {
                  weekday: "long", year: "numeric", month: "long", day: "numeric",
                })}
              </p>
            </div>

            {isDoctor && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div className="card bg-blue-50 border-blue-200">
                  <p className="text-sm text-blue-600 font-medium">Active Visits</p>
                  <p className="text-3xl font-bold text-blue-900 mt-1">
                    {activeVisits.length}
                  </p>
                </div>
                <div className="card bg-amber-50 border-amber-200">
                  <p className="text-sm text-amber-600 font-medium">Pending Lab Results</p>
                  <p className="text-3xl font-bold text-amber-900 mt-1">
                    {pendingLabs.length}
                  </p>
                </div>
                <div className="card bg-green-50 border-green-200">
                  <p className="text-sm text-green-600 font-medium">Total Patients</p>
                  <p className="text-3xl font-bold text-green-900 mt-1">
                    {(recentPatients.length > 0) ? "..." : "0"}
                  </p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              {allowedActions.map((action) => (
                <Link
                  key={action.href}
                  href={action.href}
                  className={`card border-2 ${action.color} hover:shadow-md transition-shadow`}
                >
                  <h3 className="text-lg font-semibold">{action.label}</h3>
                  <p className="text-sm mt-1 opacity-80">{action.description}</p>
                </Link>
              ))}
            </div>

            {isDoctor && activeVisits.length > 0 && (
              <div className="card mb-6">
                <h2 className="card-header">Active Visits</h2>
                <div className="space-y-2">
                  {activeVisits.map((v) => (
                    <Link
                      key={v.id}
                      href={`/patients/${v.patient}`}
                      className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                    >
                      <div>
                        <p className="font-medium text-gray-900">{v.patient_name}</p>
                        <p className="text-sm text-gray-500">{v.chief_complaint?.slice(0, 60)}</p>
                      </div>
                      <span className="text-xs text-gray-400">
                        {new Date(v.visit_date).toLocaleDateString()}
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div className="card">
              <h2 className="card-header">Recent Patients</h2>
              {isLoadingPatients ? (
                <LoadingSpinner />
              ) : recentPatients.length === 0 ? (
                <p className="text-gray-500 text-sm py-4">No patients registered yet.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="table-header">Health ID</th>
                        <th className="table-header">Name</th>
                        <th className="table-header">Gender</th>
                        <th className="table-header">Age</th>
                        <th className="table-header">Phone</th>
                        <th className="table-header"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {recentPatients.map((patient) => (
                        <tr key={patient.id} className="hover:bg-gray-50">
                          <td className="table-cell font-mono text-xs">{patient.health_id}</td>
                          <td className="table-cell font-medium">{patient.full_name}</td>
                          <td className="table-cell capitalize">{patient.gender}</td>
                          <td className="table-cell">{patient.age}</td>
                          <td className="table-cell">{patient.phone_number}</td>
                          <td className="table-cell">
                            <Link
                              href={`/patients/${patient.id}`}
                              className="text-primary-600 hover:text-primary-800 text-sm font-medium"
                            >
                              Open Profile
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
