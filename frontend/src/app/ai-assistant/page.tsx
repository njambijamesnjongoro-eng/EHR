"use client";

import { useEffect, useState } from "react";
import { aiOrchestratorApi } from "@/lib/api/aiOrchestrator";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { AIRecommendation } from "@/lib/types";

export default function AIAssistantPage() {
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [workflowData, setWorkflowData] = useState<Record<string, unknown> | null>(null);
  const [patientId, setPatientId] = useState("");
  const [generating, setGenerating] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [filter]);

  async function loadData() {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {};
      if (filter) params.recommendation_type = filter;
      const res = await aiOrchestratorApi.list(params);
      setRecommendations((res.results ?? res.data ?? []) as AIRecommendation[]);
    } catch (e) {
      console.error("Failed to load recommendations", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleAccept(id: number) {
    try {
      await aiOrchestratorApi.accept(id);
      loadData();
    } catch (e) {
      console.error("Failed to accept recommendation", e);
    }
  }

  async function handleReject(id: number) {
    const reason = prompt("Rejection reason:");
    try {
      await aiOrchestratorApi.reject(id, reason || undefined);
      loadData();
    } catch (e) {
      console.error("Failed to reject recommendation", e);
    }
  }

  async function loadWorkflow() {
    try {
      const res = await aiOrchestratorApi.workflowOptimization();
      setWorkflowData(res.data ?? null);
    } catch (e) {
      console.error("Failed to load workflow data", e);
    }
  }

  async function generateRecommendation(type: "clinical" | "preventive") {
    if (!patientId) return;
    setGenerating(type);
    try {
      if (type === "clinical") {
        await aiOrchestratorApi.generateClinical(Number(patientId));
      } else {
        await aiOrchestratorApi.generatePreventive(Number(patientId));
      }
      loadData();
    } catch (e) {
      console.error("Failed to generate recommendation", e);
    } finally {
      setGenerating(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Assistant</h1>
          <p className="text-sm text-gray-500 mt-1">AI-powered clinical recommendations and workflow optimization</p>
        </div>
        <div className="flex items-center space-x-3">
          <select value={filter} onChange={(e) => setFilter(e.target.value)} className="input w-48">
            <option value="">All Types</option>
            <option value="clinical">Clinical</option>
            <option value="medication">Medication</option>
            <option value="diagnostic">Diagnostic</option>
            <option value="follow_up">Follow Up</option>
            <option value="preventive">Preventive</option>
            <option value="lifestyle">Lifestyle</option>
          </select>
          <button onClick={loadWorkflow} className="btn btn-secondary">Workflow Opt.</button>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Generate Recommendation</h2>
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <label className="label">Patient ID</label>
            <input type="number" value={patientId} onChange={(e) => setPatientId(e.target.value)} className="input" placeholder="Enter patient ID" />
          </div>
          <button onClick={() => generateRecommendation("clinical")} disabled={!patientId || generating === "clinical"} className="btn btn-primary">
            {generating === "clinical" ? "Generating..." : "Generate Clinical"}
          </button>
          <button onClick={() => generateRecommendation("preventive")} disabled={!patientId || generating === "preventive"} className="btn btn-secondary">
            {generating === "preventive" ? "Generating..." : "Generate Preventive"}
          </button>
        </div>
      </div>

      {workflowData && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Workflow Optimization</h2>
          <pre className="text-sm text-gray-600 bg-gray-50 p-4 rounded-lg overflow-auto max-h-64">
            {JSON.stringify(workflowData, null, 2)}
          </pre>
        </div>
      )}

      {loading ? <LoadingSpinner /> : (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Recommendations ({recommendations.length})</h2>
          {recommendations.length === 0 ? (
            <div className="card">
              <p className="text-gray-500 text-sm">No recommendations generated yet</p>
            </div>
          ) : (
            recommendations.map((rec) => {
              const priorityColors: Record<string, string> = {
                information: "border-blue-200 bg-blue-50",
                suggestion: "border-gray-200 bg-gray-50",
                recommendation: "border-yellow-200 bg-yellow-50",
                alert: "border-red-200 bg-red-50",
              };
              return (
                <div key={rec.id} className={`card border-l-4 ${priorityColors[rec.priority] || "border-gray-200"}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                          rec.priority === "alert" ? "bg-red-200 text-red-800" :
                          rec.priority === "recommendation" ? "bg-yellow-200 text-yellow-800" :
                          rec.priority === "suggestion" ? "bg-gray-200 text-gray-800" :
                          "bg-blue-200 text-blue-800"
                        }`}>
                          {rec.priority.toUpperCase()}
                        </span>
                        <span className="text-xs font-medium text-gray-500">{rec.recommendation_type.replace(/_/g, " ")}</span>
                        <span className="text-xs text-gray-400">{Math.round(rec.confidence_score * 100)}% confidence</span>
                      </div>
                      <h3 className="font-semibold text-gray-900">{rec.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{rec.recommendation_text}</p>
                      {rec.clinical_rationale && (
                        <p className="text-xs text-gray-500 mt-1 italic">{rec.clinical_rationale}</p>
                      )}
                      {rec.supporting_evidence.length > 0 && (
                        <details className="mt-2">
                          <summary className="text-xs text-primary-600 cursor-pointer">Supporting Evidence</summary>
                          <ul className="mt-1 space-y-1">
                            {rec.supporting_evidence.map((e, i) => (
                              <li key={i} className="text-xs text-gray-500">- {e}</li>
                            ))}
                          </ul>
                        </details>
                      )}
                      {rec.patient_name && (
                        <p className="text-xs text-gray-400 mt-1">Patient: {rec.patient_name}</p>
                      )}
                    </div>
                    <div className="ml-4 flex flex-col items-end space-y-2">
                      {rec.is_accepted === null ? (
                        <div className="flex space-x-2">
                          <button onClick={() => handleAccept(rec.id)} className="px-3 py-1 text-xs font-medium bg-green-100 text-green-700 rounded hover:bg-green-200">Accept</button>
                          <button onClick={() => handleReject(rec.id)} className="px-3 py-1 text-xs font-medium bg-red-100 text-red-700 rounded hover:bg-red-200">Reject</button>
                        </div>
                      ) : (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          rec.is_accepted ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                        }`}>
                          {rec.is_accepted ? "Accepted" : "Rejected"}
                        </span>
                      )}
                      <span className="text-xs text-gray-400">{new Date(rec.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
