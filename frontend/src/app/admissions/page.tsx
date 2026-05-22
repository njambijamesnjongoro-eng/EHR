"use client";

import { useEffect, useState } from "react";
import { admissionsApi } from "@/lib/api/admissions";
import { patientApi } from "@/lib/api/patients";
import { useAuth } from "@/lib/auth-context";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { Ward, Bed, Admission, Patient } from "@/lib/types";

type Tab = "wards" | "active" | "history";

export default function AdmissionsPage() {
  const { user } = useAuth();
  const canManage = !!(user && ["super_admin", "hospital_admin", "doctor"].includes(user.role));

  const [tab, setTab] = useState<Tab>("active");
  const [wards, setWards] = useState<Ward[]>([]);
  const [admissions, setAdmissions] = useState<Admission[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdmit, setShowAdmit] = useState(false);

  useEffect(() => {
    loadData();
  }, [tab]);

  async function loadData() {
    setLoading(true);
    try {
      const [wRes, aRes] = await Promise.all([
        admissionsApi.listWards(),
        admissionsApi.listAdmissions({ status: tab === "history" ? undefined : "active" }),
      ]);
      setWards(wRes.data ?? []);
      setAdmissions((aRes.results ?? aRes.data ?? []) as Admission[]);
    } catch (e) {
      console.error("Failed to load admissions data", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admissions</h1>
          <p className="text-sm text-gray-500 mt-1">Manage wards, beds, and patient admissions</p>
        </div>
        {canManage && (
          <button onClick={() => setShowAdmit(true)} className="btn-primary">
            Admit Patient
          </button>
        )}
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex space-x-6">
          {[
            { key: "active" as Tab, label: "Active Admissions" },
            { key: "wards" as Tab, label: "Wards & Beds" },
            { key: "history" as Tab, label: "History" },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                tab === t.key
                  ? "border-primary-600 text-primary-700"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : tab === "wards" ? (
        <WardsView wards={wards} />
      ) : (
        <AdmissionsTable admissions={admissions} onRefresh={loadData} canManage={canManage} />
      )}

      {showAdmit && canManage && (
        <AdmitModal
          wards={wards}
          onClose={() => setShowAdmit(false)}
          onSuccess={() => { setShowAdmit(false); loadData(); }}
        />
      )}
    </div>
  );
}

function WardsView({ wards }: { wards: Ward[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {wards.map((ward) => {
        const pct = ward.capacity > 0 ? Math.round((ward.occupied_beds / ward.capacity) * 100) : 0;
        const color = pct >= 90 ? "red" : pct >= 60 ? "yellow" : "green";
        return (
          <div key={ward.id} className="card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">{ward.ward_name}</h3>
              <span className="text-xs font-medium uppercase tracking-wider text-gray-500">{ward.ward_type}</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Capacity</span>
                <span className="font-medium">{ward.capacity}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Occupied</span>
                <span className="font-medium">{ward.occupied_beds}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Available</span>
                <span className={`font-medium text-${color}-600`}>{ward.available_beds}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className={`bg-${color}-500 h-2 rounded-full transition-all`}
                  style={{ width: `${Math.min(pct, 100)}%` }}
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AdmissionsTable({
  admissions, onRefresh, canManage,
}: {
  admissions: Admission[]; onRefresh: () => void; canManage?: boolean;
}) {
  const [dischargeId, setDischargeId] = useState<number | null>(null);
  const [dischargeNotes, setDischargeNotes] = useState("");

  async function handleDischarge(id: number) {
    try {
      await admissionsApi.dischargePatient(id, dischargeNotes);
      setDischargeId(null);
      setDischargeNotes("");
      onRefresh();
    } catch (e) {
      console.error("Discharge failed", e);
    }
  }

  if (admissions.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">No admissions found</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-medium text-gray-600">Patient</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Health ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Ward</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Bed</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Admitted</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {admissions.map((adm) => (
              <tr key={adm.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{adm.patient_name}</td>
                <td className="px-4 py-3 text-gray-500">{adm.patient_health_id}</td>
                <td className="px-4 py-3">{adm.ward_name || "—"}</td>
                <td className="px-4 py-3">{adm.bed_number || "—"}</td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(adm.admission_date).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <span className={`badge-${adm.status === "active" ? "success" : adm.status === "transferred" ? "warning" : "default"} inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium`}>
                    {adm.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  {canManage && adm.status === "active" && (
                    <button
                      onClick={() => setDischargeId(adm.id)}
                      className="text-red-600 hover:text-red-800 text-sm font-medium"
                    >
                      Discharge
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {dischargeId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Discharge Patient</h3>
            <textarea
              placeholder="Discharge notes (optional)"
              value={dischargeNotes}
              onChange={(e) => setDischargeNotes(e.target.value)}
              className="input w-full mb-4"
              rows={3}
            />
            <div className="flex justify-end space-x-3">
              <button onClick={() => setDischargeId(null)} className="btn-secondary">Cancel</button>
              <button onClick={() => handleDischarge(dischargeId)} className="btn-primary bg-red-600 hover:bg-red-700">
                Confirm Discharge
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function AdmitModal({
  wards, onClose, onSuccess,
}: {
  wards: Ward[]; onClose: () => void; onSuccess: () => void;
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<number | null>(null);
  const [selectedWard, setSelectedWard] = useState("");
  const [selectedBed, setSelectedBed] = useState("");
  const [reason, setReason] = useState("");
  const [beds, setBeds] = useState<Bed[]>([]);
  const [submitting, setSubmitting] = useState(false);

  async function searchPatients(term: string) {
    setSearchTerm(term);
    if (term.length < 2) return;
    try {
      const res = await patientApi.quickSearch(term);
      setPatients(res.data ?? []);
    } catch {
      setPatients([]);
    }
  }

  async function loadBeds(wardId: string) {
    setSelectedWard(wardId);
    if (!wardId) return;
    try {
      const res = await admissionsApi.getWardBeds(Number(wardId));
      const allBeds: Bed[] = res.data ?? [];
      setBeds(allBeds.filter((b) => b.occupancy_status === "available"));
    } catch {
      setBeds([]);
    }
  }

  async function handleSubmit() {
    if (!selectedPatient || !selectedWard || !selectedBed || !reason) return;
    setSubmitting(true);
    try {
      await admissionsApi.admitPatient({
        patient: selectedPatient,
        ward: Number(selectedWard),
        bed: Number(selectedBed),
        admission_reason: reason,
      });
      onSuccess();
    } catch (e) {
      console.error("Admit failed", e);
    } finally {
      setSubmitting(false);
    }
  }

  const isValid = selectedPatient && selectedWard && selectedBed && reason;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Admit Patient</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Search Patient</label>
            <input
              type="text"
              placeholder="Search by name or health ID..."
              value={searchTerm}
              onChange={(e) => searchPatients(e.target.value)}
              className="input w-full"
            />
            {patients.length > 0 && (
              <div className="mt-1 border border-gray-200 rounded-lg max-h-40 overflow-y-auto">
                {patients.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => { setSelectedPatient(p.id); setSearchTerm(`${p.first_name} ${p.last_name} (${p.health_id})`); setPatients([]); }}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 text-sm"
                  >
                    {p.first_name} {p.last_name} <span className="text-gray-400">{p.health_id}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ward</label>
            <select
              value={selectedWard}
              onChange={(e) => loadBeds(e.target.value)}
              className="input w-full"
            >
              <option value="">Select ward...</option>
              {wards.filter((w) => w.available_beds > 0).map((w) => (
                <option key={w.id} value={w.id}>{w.ward_name} ({w.available_beds} available)</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Bed</label>
            <select
              value={selectedBed}
              onChange={(e) => setSelectedBed(e.target.value)}
              className="input w-full"
              disabled={!selectedWard}
            >
              <option value="">Select bed...</option>
              {beds.map((b) => (
                <option key={b.id} value={b.id}>{b.bed_number}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Admission Reason</label>
            <textarea
              placeholder="Reason for admission..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="input w-full"
              rows={3}
            />
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSubmit} disabled={!isValid || submitting} className="btn-primary">
            {submitting ? "Admitting..." : "Admit Patient"}
          </button>
        </div>
      </div>
    </div>
  );
}
