"use client";

import { useEffect, useState } from "react";
import { referralApi } from "@/lib/api/referrals";
import { hospitalApi } from "@/lib/api/hospitals";
import { patientApi } from "@/lib/api/patients";
import { useAuth } from "@/lib/auth-context";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { Referral, Hospital, Patient } from "@/lib/types";

type Tab = "incoming" | "outgoing" | "all";

export default function ReferralsPage() {
  const { user } = useAuth();
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("incoming");
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    loadReferrals();
  }, [tab]);

  async function loadReferrals() {
    setLoading(true);
    try {
      const [rRes, hRes] = await Promise.all([
        referralApi.list(),
        hospitalApi.list(),
      ]);
      setReferrals((rRes.data ?? rRes.results ?? []) as unknown as Referral[]);
      setHospitals((hRes.data ?? []) as Hospital[]);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const filtered = referrals.filter((r) => {
    if (tab === "incoming") return r.receiving_hospital === user?.hospital_id;
    if (tab === "outgoing") return r.referring_hospital === user?.hospital_id;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Referrals</h1>
          <p className="text-sm text-gray-500 mt-1">Cross-hospital patient referrals</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">New Referral</button>
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex space-x-6">
          {(["incoming", "outgoing", "all"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                tab === t ? "border-primary-600 text-primary-700" : "border-transparent text-gray-500"
              }`}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : filtered.length === 0 ? (
        <div className="card text-center py-12"><p className="text-gray-500">No referrals found</p></div>
      ) : (
        <div className="space-y-3">
          {filtered.map((r) => (
            <ReferralCard key={r.id} referral={r} onRefresh={loadReferrals} />
          ))}
        </div>
      )}

      {showCreate && (
        <CreateReferralModal hospitals={hospitals} onClose={() => setShowCreate(false)} onSuccess={() => { setShowCreate(false); loadReferrals(); }} />
      )}
    </div>
  );
}

function ReferralCard({ referral, onRefresh }: { referral: Referral; onRefresh: () => void }) {
  const priorityColors: Record<string, string> = {
    emergency: "bg-red-50 text-red-700", urgent: "bg-yellow-50 text-yellow-700", routine: "bg-blue-50 text-blue-700",
  };
  const statusColors: Record<string, string> = {
    pending: "bg-gray-50 text-gray-700", accepted: "bg-green-50 text-green-700",
    declined: "bg-red-50 text-red-700", completed: "bg-blue-50 text-blue-700",
    cancelled: "bg-gray-100 text-gray-400",
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3">
            <h3 className="font-semibold text-gray-900">{referral.patient_name}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${priorityColors[referral.priority]}`}>
              {referral.priority}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[referral.status]}`}>
              {referral.status}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {referral.referring_hospital_name} → {referral.receiving_hospital_name}
          </p>
          <p className="text-sm text-gray-600 mt-2">{referral.reason_for_referral.slice(0, 200)}</p>
          {referral.response_notes && (
            <div className="mt-2 p-2 bg-gray-50 rounded text-sm text-gray-600">
              <span className="font-medium">Response:</span> {referral.response_notes}
            </div>
          )}
        </div>
        <div className="flex space-x-2 ml-4">
          {referral.status === "pending" && (
            <>
              <button onClick={() => referralApi.accept(referral.id).then(onRefresh)} className="btn-primary text-xs px-3 py-1">Accept</button>
              <button onClick={() => referralApi.decline(referral.id).then(onRefresh)} className="btn-secondary text-xs px-3 py-1">Decline</button>
            </>
          )}
          {referral.status === "accepted" && (
            <button onClick={() => referralApi.complete(referral.id).then(onRefresh)} className="btn-primary text-xs px-3 py-1">Complete</button>
          )}
        </div>
      </div>
    </div>
  );
}

function CreateReferralModal({
  hospitals, onClose, onSuccess,
}: {
  hospitals: Hospital[]; onClose: () => void; onSuccess: () => void;
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<number | null>(null);
  const [receivingHospital, setReceivingHospital] = useState("");
  const [priority, setPriority] = useState("routine");
  const [reason, setReason] = useState("");
  const [summary, setSummary] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function searchPatients(term: string) {
    setSearchTerm(term);
    if (term.length < 2) return;
    try {
      const res = await patientApi.quickSearch(term);
      setPatients((res.data ?? []) as Patient[]);
    } catch {
      setPatients([]);
    }
  }

  async function handleSubmit() {
    if (!selectedPatient || !receivingHospital || !reason || !summary) return;
    setSubmitting(true);
    try {
      await referralApi.create({
        patient: selectedPatient,
        receiving_hospital: Number(receivingHospital),
        priority,
        clinical_summary: summary,
        reason_for_referral: reason,
        referral_notes: notes || undefined,
      });
      onSuccess();
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  }

  const isValid = selectedPatient && receivingHospital && reason && summary;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4">New Referral</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
            <input type="text" placeholder="Search patient..." value={searchTerm} onChange={(e) => searchPatients(e.target.value)} className="input w-full" />
            {patients.length > 0 && (
              <div className="mt-1 border rounded-lg max-h-40 overflow-y-auto">
                {patients.map((p) => (
                  <button key={p.id} onClick={() => { setSelectedPatient(p.id); setSearchTerm(`${p.first_name} ${p.last_name}`); setPatients([]); }}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 text-sm">
                    {p.first_name} {p.last_name} <span className="text-gray-400">{p.health_id}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Receiving Hospital</label>
            <select value={receivingHospital} onChange={(e) => setReceivingHospital(e.target.value)} className="input w-full">
              <option value="">Select hospital...</option>
              {hospitals.map((h) => <option key={h.id} value={h.id}>{h.hospital_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select value={priority} onChange={(e) => setPriority(e.target.value)} className="input w-full">
              <option value="routine">Routine</option>
              <option value="urgent">Urgent</option>
              <option value="emergency">Emergency</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Clinical Summary</label>
            <textarea value={summary} onChange={(e) => setSummary(e.target.value)} className="input w-full" rows={3} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reason for Referral</label>
            <textarea value={reason} onChange={(e) => setReason(e.target.value)} className="input w-full" rows={3} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Additional Notes</label>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="input w-full" rows={2} />
          </div>
        </div>
        <div className="flex justify-end space-x-3 mt-6">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSubmit} disabled={!isValid || submitting} className="btn-primary">
            {submitting ? "Submitting..." : "Submit Referral"}
          </button>
        </div>
      </div>
    </div>
  );
}
