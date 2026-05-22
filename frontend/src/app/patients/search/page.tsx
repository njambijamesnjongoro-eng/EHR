"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { patientApi } from "@/lib/api/patients";
import Sidebar from "@/components/layout/sidebar";
import Navbar from "@/components/layout/navbar";
import Pagination from "@/components/ui/pagination";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { Patient } from "@/lib/types";

export default function SearchPatientsPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [genderFilter, setGenderFilter] = useState("");
  const [bloodFilter, setBloodFilter] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchPatients = useCallback(
    async (page: number) => {
      setIsLoading(true);
      try {
        const params: Record<string, string | number | undefined> = {
          page,
          page_size: 20,
        };
        if (searchQuery.trim()) {
          params.search = searchQuery.trim();
        }
        if (genderFilter) {
          params.gender = genderFilter;
        }
        if (bloodFilter) {
          params.blood_group = bloodFilter;
        }

        const response = await patientApi.list(params);
        setPatients((response.results || []) as unknown as Patient[]);
        setTotalPages(response.total_pages || 1);
        setTotalCount(response.count || 0);
      } catch {
        setPatients([]);
      } finally {
        setIsLoading(false);
      }
    },
    [searchQuery, genderFilter, bloodFilter]
  );

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        setCurrentPage(1);
        fetchPatients(1);
      }, 300);
    }
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery, genderFilter, bloodFilter, isAuthenticated, fetchPatients]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    fetchPatients(page);
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col">
        <Navbar onMenuToggle={() => setSidebarOpen(true)} />
        <main className="flex-1 p-6 bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900">
                Search Patients
              </h1>
              <p className="text-gray-500 mt-1">
                Find patient records by name, ID, or contact details
              </p>
            </div>

            <div className="card mb-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-2">
                  <label className="label">Search</label>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="input-field"
                    placeholder="Search by name, health ID, national ID, phone..."
                    autoFocus
                  />
                </div>
                <div>
                  <label className="label">Gender</label>
                  <select
                    value={genderFilter}
                    onChange={(e) => setGenderFilter(e.target.value)}
                    className="select-field"
                  >
                    <option value="">All</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="label">Blood Group</label>
                  <select
                    value={bloodFilter}
                    onChange={(e) => setBloodFilter(e.target.value)}
                    className="select-field"
                  >
                    <option value="">All</option>
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="card-header mb-0">
                  {isLoading
                    ? "Searching..."
                    : `${totalCount} patient${totalCount !== 1 ? "s" : ""} found`}
                </h2>
              </div>

              {isLoading ? (
                <div className="py-12">
                  <LoadingSpinner />
                </div>
              ) : patients.length === 0 ? (
                <div className="text-center py-12">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-500">
                    No patients found
                  </h3>
                  <p className="mt-1 text-sm text-gray-400">
                    Try a different search term or{" "}
                    <Link
                      href="/patients/register"
                      className="text-primary-600 hover:text-primary-800"
                    >
                      register a new patient
                    </Link>
                  </p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="table-header">Health ID</th>
                          <th className="table-header">Name</th>
                          <th className="table-header">Gender</th>
                          <th className="table-header">Age</th>
                          <th className="table-header">Blood</th>
                          <th className="table-header">Phone</th>
                          <th className="table-header"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {patients.map((patient) => (
                          <tr
                            key={patient.id}
                            className="hover:bg-gray-50 cursor-pointer"
                            onClick={() =>
                              router.push(`/patients/${patient.id}`)
                            }
                          >
                            <td className="table-cell font-mono text-xs">
                              {patient.health_id}
                            </td>
                            <td className="table-cell font-medium">
                              {patient.full_name}
                            </td>
                            <td className="table-cell capitalize">
                              {patient.gender}
                            </td>
                            <td className="table-cell">{patient.age}</td>
                            <td className="table-cell">
                              <span className="badge-info">
                                {patient.blood_group}
                              </span>
                            </td>
                            <td className="table-cell">
                              {patient.phone_number}
                            </td>
                            <td className="table-cell">
                              <Link
                                href={`/patients/${patient.id}`}
                                className="text-primary-600 hover:text-primary-800 text-sm font-medium"
                                onClick={(e) => e.stopPropagation()}
                              >
                                View Profile
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                  />
                </>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
