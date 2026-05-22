"use client";

import { useEffect, useState } from "react";
import { imagingApi } from "@/lib/api/imaging";
import { patientApi } from "@/lib/api/patients";
import { useAuth } from "@/lib/auth-context";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { ImagingRequest, ImagingResult, Patient } from "@/lib/types";

type Tab = "requests" | "results";
type FilterStatus = "all" | "requested" | "scheduled" | "completed" | "cancelled";

export default function ImagingPage() {
  const { user } = useAuth();
  const canRequest = !!(user && ["super_admin", "hospital_admin", "doctor"].includes(user.role));
  const canUpload = !!(user && ["super_admin", "hospital_admin", "radiologist"].includes(user.role));

  const [tab, setTab] = useState<Tab>("requests");
  const [requests, setRequests] = useState<ImagingRequest[]>([]);
  const [results, setResults] = useState<ImagingResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterStatus>("all");
  const [showRequest, setShowRequest] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    loadData();
  }, [tab, filter]);

  async function loadData() {
    setLoading(true);
    try {
      if (tab === "requests") {
        const params: Record<string, string> = {};
        if (filter !== "all") params.status = filter;
        const res = await imagingApi.listRequests(params);
        setRequests((res.results ?? res.data ?? []) as ImagingRequest[]);
      } else {
        const res = await imagingApi.listResults();
        setResults((res.results ?? res.data ?? []) as ImagingResult[]);
      }
    } catch (e) {
      console.error("Failed to load imaging data", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Imaging & Radiology</h1>
          <p className="text-sm text-gray-500 mt-1">Manage imaging requests and results</p>
        </div>
        <div className="flex space-x-3">
          {canRequest && (
            <button onClick={() => setShowRequest(true)} className="btn-primary">
              New Request
            </button>
          )}
          {canUpload && (
            <button onClick={() => setShowUpload(true)} className="btn-secondary">
              Upload Result
            </button>
          )}
        </div>
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex space-x-6">
          {[
            { key: "requests" as Tab, label: "Requests" },
            { key: "results" as Tab, label: "Results" },
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

      {tab === "requests" && (
        <div className="flex space-x-2">
          {(["all", "requested", "scheduled", "completed", "cancelled"] as FilterStatus[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-sm rounded-lg font-medium transition-colors ${
                filter === f
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              {f.replace(/\b\w/g, (c) => c.toUpperCase())}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : tab === "requests" ? (
        <RequestsTable requests={requests} />
      ) : (
        <ResultsTable results={results} />
      )}

      {showRequest && canRequest && (
        <RequestModal
          onClose={() => setShowRequest(false)}
          onSuccess={() => { setShowRequest(false); loadData(); }}
        />
      )}

      {showUpload && canUpload && (
        <UploadModal
          requests={requests.filter((r) => r.status !== "completed" && r.status !== "cancelled")}
          onClose={() => setShowUpload(false)}
          onSuccess={() => { setShowUpload(false); loadData(); }}
        />
      )}
    </div>
  );
}

function RequestsTable({ requests }: { requests: ImagingRequest[] }) {
  if (requests.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">No imaging requests found</p>
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
              <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Region</th>
              <th className="text-center px-4 py-3 font-medium text-gray-600">Priority</th>
              <th className="text-center px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Requested By</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {requests.map((req) => (
              <tr key={req.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{req.patient_name}</td>
                <td className="px-4 py-3">
                  <span className="uppercase text-xs font-medium">{req.imaging_type.replace("_", " ")}</span>
                </td>
                <td className="px-4 py-3 text-gray-500">{req.region_examined || "—"}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    req.priority === "stat" ? "bg-red-50 text-red-700" :
                    req.priority === "urgent" ? "bg-yellow-50 text-yellow-700" :
                    "bg-blue-50 text-blue-700"
                  }`}>
                    {req.priority}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    req.status === "completed" ? "bg-green-50 text-green-700" :
                    req.status === "cancelled" ? "bg-red-50 text-red-700" :
                    req.status === "scheduled" ? "bg-blue-50 text-blue-700" :
                    "bg-gray-50 text-gray-700"
                  }`}>
                    {req.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">{req.requested_by_name}</td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(req.requested_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ResultsTable({ results }: { results: ImagingResult[] }) {
  if (results.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">No imaging results found</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Findings</th>
              <th className="text-center px-4 py-3 font-medium text-gray-600">Abnormal</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Radiologist</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {results.map((res) => (
              <tr key={res.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900 uppercase text-xs">
                  {res.imaging_type.replace("_", " ")}
                </td>
                <td className="px-4 py-3 text-gray-500 max-w-xs truncate">{res.findings}</td>
                <td className="px-4 py-3 text-center">
                  {res.is_abnormal ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700">
                      Yes
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700">
                      No
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-500">{res.radiologist_name || "—"}</td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(res.result_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RequestModal({
  onClose, onSuccess,
}: {
  onClose: () => void; onSuccess: () => void;
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<number | null>(null);
  const [imagingType, setImagingType] = useState("xray");
  const [priority, setPriority] = useState("routine");
  const [region, setRegion] = useState("");
  const [history, setHistory] = useState("");
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

  async function handleSubmit() {
    if (!selectedPatient) return;
    setSubmitting(true);
    try {
      await imagingApi.createRequest({
        visit: 0,
        patient: selectedPatient,
        imaging_type: imagingType,
        priority,
        clinical_history: history || undefined,
        region_examined: region || undefined,
      });
      onSuccess();
    } catch (e) {
      console.error("Create request failed", e);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">New Imaging Request</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
            <input
              type="text"
              placeholder="Search patient..."
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Imaging Type</label>
              <select value={imagingType} onChange={(e) => setImagingType(e.target.value)} className="input w-full">
                <option value="xray">X-Ray</option>
                <option value="mri">MRI</option>
                <option value="ct_scan">CT Scan</option>
                <option value="ultrasound">Ultrasound</option>
                <option value="mammography">Mammography</option>
                <option value="pet_scan">PET Scan</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
              <select value={priority} onChange={(e) => setPriority(e.target.value)} className="input w-full">
                <option value="routine">Routine</option>
                <option value="urgent">Urgent</option>
                <option value="stat">STAT</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Region Examined</label>
            <input
              type="text"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              placeholder="e.g., Chest, Abdomen, Brain..."
              className="input w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Clinical History</label>
            <textarea
              value={history}
              onChange={(e) => setHistory(e.target.value)}
              className="input w-full"
              rows={3}
              placeholder="Relevant clinical history..."
            />
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSubmit} disabled={!selectedPatient || submitting} className="btn-primary">
            {submitting ? "Submitting..." : "Submit Request"}
          </button>
        </div>
      </div>
    </div>
  );
}

function UploadModal({
  requests, onClose, onSuccess,
}: {
  requests: ImagingRequest[]; onClose: () => void; onSuccess: () => void;
}) {
  const [selectedRequest, setSelectedRequest] = useState("");
  const [findings, setFindings] = useState("");
  const [impression, setImpression] = useState("");
  const [report, setReport] = useState("");
  const [isAbnormal, setIsAbnormal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    if (!selectedRequest || !findings) return;
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("imaging_request", selectedRequest);
      formData.append("findings", findings);
      if (impression) formData.append("impression", impression);
      if (report) formData.append("report", report);
      formData.append("is_abnormal", String(isAbnormal));
      await imagingApi.uploadResult(formData);
      onSuccess();
    } catch (e) {
      console.error("Upload result failed", e);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Imaging Result</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Imaging Request</label>
            <select
              value={selectedRequest}
              onChange={(e) => setSelectedRequest(e.target.value)}
              className="input w-full"
            >
              <option value="">Select request...</option>
              {requests.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.patient_name} - {r.imaging_type.replace("_", " ").toUpperCase()} ({r.requested_at?.slice(0, 10)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Findings</label>
            <textarea
              value={findings}
              onChange={(e) => setFindings(e.target.value)}
              className="input w-full"
              rows={4}
              placeholder="Radiological findings..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Impression</label>
            <textarea
              value={impression}
              onChange={(e) => setImpression(e.target.value)}
              className="input w-full"
              rows={3}
              placeholder="Clinical impression..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Report</label>
            <textarea
              value={report}
              onChange={(e) => setReport(e.target.value)}
              className="input w-full"
              rows={4}
              placeholder="Full report..."
            />
          </div>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={isAbnormal}
              onChange={(e) => setIsAbnormal(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">Mark as abnormal</span>
          </label>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSubmit} disabled={!selectedRequest || !findings || submitting} className="btn-primary">
            {submitting ? "Uploading..." : "Upload Result"}
          </button>
        </div>
      </div>
    </div>
  );
}
