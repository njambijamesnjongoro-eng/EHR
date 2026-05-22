"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { patientApi } from "@/lib/api/patients";
import { clinicalApi } from "@/lib/api/clinical";
import { labApi } from "@/lib/api/labs";
import Sidebar from "@/components/layout/sidebar";
import Navbar from "@/components/layout/navbar";
import LoadingSpinner from "@/components/ui/loading-spinner";
import VisitTab from "@/components/clinical/visit-tab";
import VitalsTab from "@/components/clinical/vitals-tab";
import DiagnosisTab from "@/components/clinical/diagnosis-tab";
import PrescriptionTab from "@/components/clinical/prescription-tab";
import LabsTab from "@/components/clinical/labs-tab";
import TimelineTab from "@/components/clinical/timeline-tab";
import type { Patient, Visit, VitalSignRecord, Diagnosis, Prescription, LabRequest } from "@/lib/types";

type Tab = "info" | "visit" | "vitals" | "diagnosis" | "prescription" | "labs" | "timeline";

export default function PatientProfilePage() {
  const { id } = useParams<{ id: string }>();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("info");
  const [loadedTabs, setLoadedTabs] = useState<Set<Tab>>(new Set<Tab>(["info"]));

  const [editForm, setEditForm] = useState<Record<string, string>>({});
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState("");

  const [visits, setVisits] = useState<Visit[]>([]);
  const [vitals, setVitals] = useState<VitalSignRecord[]>([]);
  const [diagnoses, setDiagnoses] = useState<Diagnosis[]>([]);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [labRequests, setLabRequests] = useState<LabRequest[]>([]);
  const [clinicalLoading, setClinicalLoading] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated && id) {
      patientApi.get(id)
        .then((res) => setPatient(res.data!))
        .catch(() => router.push("/patients/search"))
        .finally(() => setIsLoading(false));
    }
  }, [isAuthenticated, id, router]);

  const loadClinicalData = useCallback(async () => {
    if (!patient || clinicalLoading) return;
    setClinicalLoading(true);
    try {
      const [visitsRes, vitalsRes, diagnosesRes, prescriptionsRes, labsRes] = await Promise.all([
        clinicalApi.listVisits({ patient: patient.id }),
        clinicalApi.listVitals({ patient: patient.id }),
        clinicalApi.listDiagnoses({ patient: patient.id }),
        clinicalApi.listPrescriptions({ patient: patient.id }),
        labApi.listRequests({ patient: patient.id }),
      ]);
      setVisits((visitsRes.results || []) as unknown as Visit[]);
      setVitals((vitalsRes.results || []) as unknown as VitalSignRecord[]);
      setDiagnoses((diagnosesRes.results || []) as unknown as Diagnosis[]);
      setPrescriptions((prescriptionsRes.results || []) as unknown as Prescription[]);
      setLabRequests((labsRes.results || []) as unknown as LabRequest[]);
    } catch {
      // handle errors silently
    } finally {
      setClinicalLoading(false);
    }
  }, [patient, clinicalLoading]);

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    if (!loadedTabs.has(tab)) {
      setLoadedTabs((prev) => new Set(prev).add(tab));
      if (tab !== "info" && tab !== "timeline") {
        loadClinicalData();
      }
    }
  };

  const startEdit = () => {
    if (!patient) return;
    setEditForm({
      first_name: patient.first_name, last_name: patient.last_name, national_id: patient.national_id || "",
      date_of_birth: patient.date_of_birth, gender: patient.gender, phone_number: patient.phone_number,
      email: patient.email || "", address: patient.address || "",
      emergency_contact_name: patient.emergency_contact_name || "",
      emergency_contact_phone: patient.emergency_contact_phone || "",
      blood_group: patient.blood_group, allergies: patient.allergies || "",
      chronic_conditions: patient.chronic_conditions || "",
    });
    setIsEditing(true);
  };

  const handleEditChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setEditForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSaveEdit = async () => {
    setSaveError(""); setSaveSuccess(""); setIsSaving(true);
    try {
      const response = await patientApi.update(id, editForm);
      setPatient(response.data!);
      setIsEditing(false);
      setSaveSuccess("Patient updated successfully");
      setTimeout(() => setSaveSuccess(""), 3000);
    } catch {
      setSaveError("Failed to update patient");
    } finally {
      setIsSaving(false);
    }
  };

  if (authLoading || isLoading || !patient) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const bloodGroupColors: Record<string, string> = {
    "A+": "bg-red-100 text-red-800", "A-": "bg-red-50 text-red-700",
    "B+": "bg-blue-100 text-blue-800", "B-": "bg-blue-50 text-blue-700",
    "AB+": "bg-purple-100 text-purple-800", "AB-": "bg-purple-50 text-purple-700",
    "O+": "bg-green-100 text-green-800", "O-": "bg-green-50 text-green-700",
    unknown: "bg-gray-100 text-gray-700",
  };

  const tabLabels: Record<Tab, string> = {
    info: "Info", visit: "Visit", vitals: "Vitals",
    diagnosis: "Diagnosis", prescription: "Rx", labs: "Labs", timeline: "Timeline",
  };

  const tabColors: Record<Tab, string> = {
    info: "text-primary-600 border-primary-600",
    visit: "text-blue-600 border-blue-600",
    vitals: "text-green-600 border-green-600",
    diagnosis: "text-red-600 border-red-600",
    prescription: "text-purple-600 border-purple-600",
    labs: "text-amber-600 border-amber-600",
    timeline: "text-gray-600 border-gray-600",
  };

  return (
    <div className="min-h-screen flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col">
        <Navbar onMenuToggle={() => setSidebarOpen(true)} />
        <main className="flex-1 p-6 bg-gray-50">
          <div className="max-w-6xl mx-auto">
            <button
              onClick={() => router.push("/patients/search")}
              className="text-sm text-gray-500 hover:text-gray-700 mb-4 flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to search
            </button>

            {saveSuccess && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm mb-4">
                {saveSuccess}
              </div>
            )}

            <div className="card mb-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-14 h-14 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-primary-700 font-bold text-lg">
                      {patient.first_name[0]}{patient.last_name[0]}
                    </span>
                  </div>
                  <div>
                    <h1 className="text-xl font-bold text-gray-900">{patient.full_name}</h1>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-sm font-mono text-gray-500">{patient.health_id}</span>
                      <span className={`badge ${bloodGroupColors[patient.blood_group] || "bg-gray-100"}`}>
                        {patient.blood_group}
                      </span>
                      <span className="text-xs text-gray-400">Age: {patient.age}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2 mt-4 sm:mt-0">
                  <button onClick={startEdit} className="btn-secondary text-sm">Edit Profile</button>
                </div>
              </div>
            </div>

            <div className="border-b border-gray-200 mb-6 overflow-x-auto">
              <nav className="flex space-x-1 min-w-max">
                {(Object.keys(tabLabels) as Tab[]).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => handleTabChange(tab)}
                    className={`px-3 py-2.5 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                      activeTab === tab
                        ? tabColors[tab]
                        : "text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300"
                    }`}
                  >
                    {tabLabels[tab]}
                  </button>
                ))}
              </nav>
            </div>

            {activeTab === "info" && !isEditing && (
              <div className="card">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-3">Personal Details</h3>
                    <dl className="space-y-3">
                      <div><dt className="text-xs text-gray-400">Gender</dt><dd className="text-sm font-medium capitalize">{patient.gender}</dd></div>
                      <div><dt className="text-xs text-gray-400">Date of Birth</dt><dd className="text-sm font-medium">{new Date(patient.date_of_birth).toLocaleDateString()} (Age: {patient.age})</dd></div>
                      <div><dt className="text-xs text-gray-400">National ID</dt><dd className="text-sm font-medium">{patient.national_id || "N/A"}</dd></div>
                    </dl>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-3">Contact</h3>
                    <dl className="space-y-3">
                      <div><dt className="text-xs text-gray-400">Phone</dt><dd className="text-sm font-medium">{patient.phone_number}</dd></div>
                      <div><dt className="text-xs text-gray-400">Email</dt><dd className="text-sm font-medium">{patient.email || "N/A"}</dd></div>
                      <div><dt className="text-xs text-gray-400">Address</dt><dd className="text-sm font-medium">{patient.address || "N/A"}</dd></div>
                    </dl>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-3">Emergency Contact</h3>
                    <dl className="space-y-3">
                      <div><dt className="text-xs text-gray-400">Name</dt><dd className="text-sm font-medium">{patient.emergency_contact_name || "N/A"}</dd></div>
                      <div><dt className="text-xs text-gray-400">Phone</dt><dd className="text-sm font-medium">{patient.emergency_contact_phone || "N/A"}</dd></div>
                    </dl>
                  </div>
                </div>
                {(patient.allergies || patient.chronic_conditions) && (
                  <div className="border-t border-gray-200 pt-6 mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                    {patient.allergies && (
                      <div>
                        <h3 className="text-sm font-medium text-gray-500 mb-2">Allergies</h3>
                        <div className="flex flex-wrap gap-2">
                          {patient.allergies.split(",").map((a, i) => (
                            <span key={i} className="badge-danger">{a.trim()}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {patient.chronic_conditions && (
                      <div>
                        <h3 className="text-sm font-medium text-gray-500 mb-2">Chronic Conditions</h3>
                        <div className="flex flex-wrap gap-2">
                          {patient.chronic_conditions.split(",").map((c, i) => (
                            <span key={i} className="badge-warning">{c.trim()}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                <div className="border-t border-gray-200 pt-4 mt-6">
                  <p className="text-xs text-gray-400">
                    Registered: {new Date(patient.created_at).toLocaleString()} | Updated: {new Date(patient.updated_at).toLocaleString()}
                  </p>
                </div>
              </div>
            )}

            {isEditing && (
              <div className="card">
                <h2 className="card-header">Edit Patient</h2>
                {saveError && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">{saveError}</div>}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {["first_name","last_name","national_id"].map((f) => (
                    <div key={f}>
                      <label className="label capitalize">{f.replace("_"," ")}</label>
                      <input name={f} value={editForm[f]||""} onChange={handleEditChange} className="input-field" />
                    </div>
                  ))}
                  <div>
                    <label className="label">Date of Birth</label>
                    <input name="date_of_birth" type="date" value={editForm.date_of_birth||""} onChange={handleEditChange} className="input-field" />
                  </div>
                  <div>
                    <label className="label">Gender</label>
                    <select name="gender" value={editForm.gender||"male"} onChange={handleEditChange} className="select-field">
                      <option value="male">Male</option><option value="female">Female</option><option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Blood Group</label>
                    <select name="blood_group" value={editForm.blood_group||"unknown"} onChange={handleEditChange} className="select-field">
                      {["A+","A-","B+","B-","AB+","AB-","O+","O-","unknown"].map(b=><option key={b} value={b}>{b}</option>)}
                    </select>
                  </div>
                  <div><label className="label">Phone</label><input name="phone_number" value={editForm.phone_number||""} onChange={handleEditChange} className="input-field" /></div>
                  <div><label className="label">Email</label><input name="email" type="email" value={editForm.email||""} onChange={handleEditChange} className="input-field" /></div>
                  <div className="md:col-span-2"><label className="label">Address</label><textarea name="address" rows={2} value={editForm.address||""} onChange={handleEditChange} className="input-field" /></div>
                  <div><label className="label">Emergency Contact</label><input name="emergency_contact_name" value={editForm.emergency_contact_name||""} onChange={handleEditChange} className="input-field" /></div>
                  <div><label className="label">Emergency Phone</label><input name="emergency_contact_phone" value={editForm.emergency_contact_phone||""} onChange={handleEditChange} className="input-field" /></div>
                  <div><label className="label">Allergies</label><textarea name="allergies" rows={2} value={editForm.allergies||""} onChange={handleEditChange} className="input-field" /></div>
                  <div><label className="label">Chronic Conditions</label><textarea name="chronic_conditions" rows={2} value={editForm.chronic_conditions||""} onChange={handleEditChange} className="input-field" /></div>
                </div>
                <div className="flex items-center justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
                  <button onClick={() => setIsEditing(false)} className="btn-secondary">Cancel</button>
                  <button onClick={handleSaveEdit} disabled={isSaving} className="btn-primary">
                    {isSaving ? <LoadingSpinner size="sm" /> : "Save Changes"}
                  </button>
                </div>
              </div>
            )}

            {activeTab === "visit" && loadedTabs.has("visit") && (
              <VisitTab patient={patient} visits={visits} isLoading={clinicalLoading} onRefresh={loadClinicalData} />
            )}
            {activeTab === "vitals" && loadedTabs.has("vitals") && (
              <VitalsTab patient={patient} visits={visits} vitals={vitals} isLoading={clinicalLoading} onRefresh={loadClinicalData} />
            )}
            {activeTab === "diagnosis" && loadedTabs.has("diagnosis") && (
              <DiagnosisTab patient={patient} visits={visits} diagnoses={diagnoses} isLoading={clinicalLoading} onRefresh={loadClinicalData} />
            )}
            {activeTab === "prescription" && loadedTabs.has("prescription") && (
              <PrescriptionTab patient={patient} visits={visits} prescriptions={prescriptions} isLoading={clinicalLoading} onRefresh={loadClinicalData} />
            )}
            {activeTab === "labs" && loadedTabs.has("labs") && (
              <LabsTab patient={patient} visits={visits} labRequests={labRequests} isLoading={clinicalLoading} onRefresh={loadClinicalData} />
            )}
            {activeTab === "timeline" && <TimelineTab patient={patient} />}
          </div>
        </main>
      </div>
    </div>
  );
}
