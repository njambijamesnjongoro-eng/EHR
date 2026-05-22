"use client";

import { useEffect, useState } from "react";
import { aiGovernanceApi } from "@/lib/api/aiGovernance";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { AIModelRegistry, ModelGovernanceReport } from "@/lib/types";

export default function AIGovernancePage() {
  const [models, setModels] = useState<AIModelRegistry[]>([]);
  const [selectedModel, setSelectedModel] = useState<number | null>(null);
  const [governanceReport, setGovernanceReport] = useState<ModelGovernanceReport | null>(null);
  const [auditEntries, setAuditEntries] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("");

  useEffect(() => {
    loadModels();
  }, [filterStatus]);

  async function loadModels() {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {};
      if (filterStatus) params.status = filterStatus;
      const res = await aiGovernanceApi.listModels(params);
      setModels((res.results ?? res.data ?? []) as AIModelRegistry[]);
    } catch (e) {
      console.error("Failed to load models", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleModelClick(id: number) {
    setSelectedModel(id);
    setGovernanceReport(null);
    try {
      const [detailRes, govRes] = await Promise.all([
        aiGovernanceApi.modelDetail(id),
        aiGovernanceApi.governanceReport(id),
      ]);
      const model = detailRes.data ?? (detailRes as unknown as AIModelRegistry);
      if (govRes.data) setGovernanceReport(govRes.data);
    } catch (e) {
      console.error("Failed to load model details", e);
    }
  }

  async function handleUpdateStatus(id: number, status: string) {
    try {
      await aiGovernanceApi.updateStatus(id, status);
      loadModels();
      if (selectedModel === id) handleModelClick(id);
    } catch (e) {
      console.error("Failed to update model status", e);
    }
  }

  async function handleAudit() {
    try {
      const res = await aiGovernanceApi.auditTrail();
      setAuditEntries((res.results ?? res.data ?? []) as Record<string, unknown>[]);
    } catch (e) {
      console.error("Failed to load audit trail", e);
    }
  }

  const statusColors: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    inactive: "bg-gray-100 text-gray-600",
    deprecated: "bg-red-100 text-red-800",
    testing: "bg-yellow-100 text-yellow-800",
    pending: "bg-blue-100 text-blue-800",
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Governance Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Model registry, governance oversight, and compliance auditing</p>
        </div>
        <div className="flex items-center space-x-3">
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="input w-44">
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="testing">Testing</option>
            <option value="pending">Pending</option>
            <option value="deprecated">Deprecated</option>
            <option value="inactive">Inactive</option>
          </select>
          <button onClick={handleAudit} className="btn btn-secondary">Audit Trail</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Model Registry ({models.length})</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left text-gray-500">
                  <th className="pb-2 pr-4 font-medium">Model Name</th>
                  <th className="pb-2 pr-4 font-medium">Version</th>
                  <th className="pb-2 pr-4 font-medium">Type</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 pr-4 font-medium">Governance</th>
                  <th className="pb-2 pr-4 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.id} className={`border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${selectedModel === model.id ? "bg-primary-50" : ""}`} onClick={() => handleModelClick(model.id)}>
                    <td className="py-2 pr-4 font-medium text-gray-900">{model.model_name}</td>
                    <td className="py-2 pr-4 text-gray-600">{model.model_version}</td>
                    <td className="py-2 pr-4 text-gray-600">{model.model_type}</td>
                    <td className="py-2 pr-4"><span className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusColors[model.status] || "bg-gray-100"}`}>{model.status}</span></td>
                    <td className="py-2 pr-4">
                      <span className={`text-xs font-medium ${model.governance_approval ? "text-green-600" : "text-yellow-600"}`}>
                        {model.governance_approval ? "Approved" : "Pending"}
                      </span>
                    </td>
                    <td className="py-2 pr-4">
                      <select
                        value={model.status}
                        onChange={(e) => { e.stopPropagation(); handleUpdateStatus(model.id, e.target.value); }}
                        className="text-xs border border-gray-300 rounded px-1 py-0.5"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <option value="active">Active</option>
                        <option value="testing">Testing</option>
                        <option value="pending">Pending</option>
                        <option value="deprecated">Deprecated</option>
                        <option value="inactive">Inactive</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Model Details</h2>
          {selectedModel && governanceReport ? (
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-gray-500 text-xs">Model</p>
                <p className="font-medium">{governanceReport.model_name} v{governanceReport.model_version}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Type</p>
                <p>{governanceReport.model_type}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Status</p>
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusColors[governanceReport.status] || "bg-gray-100"}`}>{governanceReport.status}</span>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Governance Approval</p>
                <p className={`font-medium ${governanceReport.governance_approval ? "text-green-600" : "text-yellow-600"}`}>{governanceReport.governance_approval ? "Approved" : "Not Approved"}</p>
              </div>
              <div className="border-t border-gray-200 pt-3">
                <p className="text-gray-500 text-xs mb-2">Usage Metrics</p>
                <div className="flex justify-between"><span className="text-gray-500">Total Inferences</span><span className="font-medium">{governanceReport.total_inferences?.toLocaleString() || 0}</span></div>
                <div className="flex justify-between mt-1"><span className="text-gray-500">Avg Confidence</span><span className="font-medium">{(governanceReport.avg_confidence * 100)?.toFixed(1) || "—"}%</span></div>
                <div className="flex justify-between mt-1"><span className="text-gray-500">Audit Entries</span><span className="font-medium">{governanceReport.audit_entries}</span></div>
                <div className="flex justify-between mt-1"><span className="text-gray-500">Last Used</span><span className="font-medium">{governanceReport.last_used ? new Date(governanceReport.last_used).toLocaleDateString() : "Never"}</span></div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Select a model to view details</p>
          )}
        </div>
      </div>

      {auditEntries.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Audit Trail ({auditEntries.length})</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left text-gray-500">
                  <th className="pb-2 pr-4 font-medium">Timestamp</th>
                  <th className="pb-2 pr-4 font-medium">Action</th>
                  <th className="pb-2 pr-4 font-medium">User</th>
                  <th className="pb-2 pr-4 font-medium">Details</th>
                </tr>
              </thead>
              <tbody>
                {auditEntries.map((entry, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-2 pr-4 text-gray-500">{new Date((entry as { timestamp?: string }).timestamp || "").toLocaleString()}</td>
                    <td className="py-2 pr-4 text-gray-900 font-medium">{(entry as { action?: string }).action}</td>
                    <td className="py-2 pr-4 text-gray-600">{(entry as { user?: string | number }).user?.toString() || "—"}</td>
                    <td className="py-2 pr-4 text-gray-500 max-w-xs truncate">{(entry as { details?: string }).details || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
