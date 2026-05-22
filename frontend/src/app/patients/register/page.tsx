"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { patientApi } from "@/lib/api/patients";
import Sidebar from "@/components/layout/sidebar";
import Navbar from "@/components/layout/navbar";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { PatientFormData } from "@/lib/types";

const bloodGroups = [
  "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "unknown",
];

const initialFormData: PatientFormData = {
  first_name: "",
  last_name: "",
  national_id: "",
  date_of_birth: "",
  gender: "male",
  phone_number: "",
  email: "",
  address: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
  blood_group: "unknown",
  allergies: "",
  chronic_conditions: "",
};

export default function RegisterPatientPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [formData, setFormData] = useState<PatientFormData>(initialFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setIsSubmitting(true);

    try {
      const response = await patientApi.create(formData);
      const patient = response.data;
      setSuccess(`Patient registered successfully! Health ID: ${patient?.health_id}`);
      setFormData(initialFormData);
    } catch (err: unknown) {
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } };
        setError(
          axiosErr.response?.data?.message || "Failed to register patient"
        );
      } else {
        setError("An error occurred. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
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
          <div className="max-w-3xl mx-auto">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900">
                Register New Patient
              </h1>
              <p className="text-gray-500 mt-1">
                Enter patient details to create a new record
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-6">
                {error}
              </div>
            )}

            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm mb-6">
                {success}
              </div>
            )}

            <form onSubmit={handleSubmit} className="card space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label" htmlFor="first_name">
                    First Name *
                  </label>
                  <input
                    id="first_name"
                    name="first_name"
                    type="text"
                    required
                    value={formData.first_name}
                    onChange={handleChange}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="label" htmlFor="last_name">
                    Last Name *
                  </label>
                  <input
                    id="last_name"
                    name="last_name"
                    type="text"
                    required
                    value={formData.last_name}
                    onChange={handleChange}
                    className="input-field"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label" htmlFor="national_id">
                    National ID
                  </label>
                  <input
                    id="national_id"
                    name="national_id"
                    type="text"
                    value={formData.national_id}
                    onChange={handleChange}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="label" htmlFor="date_of_birth">
                    Date of Birth *
                  </label>
                  <input
                    id="date_of_birth"
                    name="date_of_birth"
                    type="date"
                    required
                    value={formData.date_of_birth}
                    onChange={handleChange}
                    className="input-field"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label" htmlFor="gender">
                    Gender *
                  </label>
                  <select
                    id="gender"
                    name="gender"
                    required
                    value={formData.gender}
                    onChange={handleChange}
                    className="select-field"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="label" htmlFor="blood_group">
                    Blood Group
                  </label>
                  <select
                    id="blood_group"
                    name="blood_group"
                    value={formData.blood_group}
                    onChange={handleChange}
                    className="select-field"
                  >
                    {bloodGroups.map((bg) => (
                      <option key={bg} value={bg}>
                        {bg}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label" htmlFor="phone_number">
                    Phone Number *
                  </label>
                  <input
                    id="phone_number"
                    name="phone_number"
                    type="tel"
                    required
                    value={formData.phone_number}
                    onChange={handleChange}
                    className="input-field"
                    placeholder="+1234567890"
                  />
                </div>
                <div>
                  <label className="label" htmlFor="email">
                    Email
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="input-field"
                  />
                </div>
              </div>

              <div>
                <label className="label" htmlFor="address">
                  Address
                </label>
                <textarea
                  id="address"
                  name="address"
                  rows={2}
                  value={formData.address}
                  onChange={handleChange}
                  className="input-field"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label" htmlFor="emergency_contact_name">
                    Emergency Contact Name
                  </label>
                  <input
                    id="emergency_contact_name"
                    name="emergency_contact_name"
                    type="text"
                    value={formData.emergency_contact_name}
                    onChange={handleChange}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="label" htmlFor="emergency_contact_phone">
                    Emergency Contact Phone
                  </label>
                  <input
                    id="emergency_contact_phone"
                    name="emergency_contact_phone"
                    type="tel"
                    value={formData.emergency_contact_phone}
                    onChange={handleChange}
                    className="input-field"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label" htmlFor="allergies">
                    Allergies (comma-separated)
                  </label>
                  <textarea
                    id="allergies"
                    name="allergies"
                    rows={2}
                    value={formData.allergies}
                    onChange={handleChange}
                    className="input-field"
                    placeholder="e.g. Penicillin, Peanuts"
                  />
                </div>
                <div>
                  <label className="label" htmlFor="chronic_conditions">
                    Chronic Conditions (comma-separated)
                  </label>
                  <textarea
                    id="chronic_conditions"
                    name="chronic_conditions"
                    rows={2}
                    value={formData.chronic_conditions}
                    onChange={handleChange}
                    className="input-field"
                    placeholder="e.g. Diabetes, Hypertension"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-primary flex items-center"
                >
                  {isSubmitting ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    "Register Patient"
                  )}
                </button>
              </div>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}
