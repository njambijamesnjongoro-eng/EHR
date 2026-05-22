"use client";

import { useEffect, useState } from "react";
import { aiApi } from "@/lib/api/ai";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { AIInsight } from "@/lib/types";

export default function AIInsightsPage() {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    loadData();
  }, [filter]);

  async function loadData() {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filter) params.insight_type = filter;
      const res = await aiApi.listInsights(params);
      setInsights((res.results ?? res.data ?? []) as AIInsight[]);
    } catch (e) {
      console.error("Failed to load AI insights", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Clinical Insights</h1>
          <p className="text-sm text-gray-500 mt-1">AI-assisted clinical decision support - all insights require clinician review</p>
        </div>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} className="input w-48">
          <option value="">All Types</option>
          <option value="risk_assessment">Risk Assessment</option>
          <option value="medication_check">Medication Check</option>
          <option value="deterioration_alert">Deterioration Alert</option>
          <option value="diagnosis_suggestion">Diagnosis Suggestion</option>
        </select>
      </div>

      {loading ? <LoadingSpinner /> : (
        <div className="card">
          {insights.length === 0 ? (
            <p className="text-gray-500 text-sm">No AI insights generated yet</p>
          ) : (
            <div className="space-y-4">
              {insights.map((insight) => (
                <div key={insight.id} className={`p-4 rounded-lg border ${
                  insight.confidence === "high" ? "border-green-200 bg-green-50" :
                  insight.confidence === "medium" ? "border-yellow-200 bg-yellow-50" :
                  "border-gray-200 bg-gray-50"
                }`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                          insight.confidence === "high" ? "bg-green-200 text-green-800" :
                          insight.confidence === "medium" ? "bg-yellow-200 text-yellow-800" :
                          "bg-gray-200 text-gray-800"
                        }`}>
                          {insight.confidence.toUpperCase()} {Math.round(insight.confidence_score * 100)}%
                        </span>
                        <span className="text-xs font-medium text-gray-500">{insight.insight_type.replace(/_/g, " ")}</span>
                        {insight.source_service && (
                          <span className="text-xs text-gray-400">{insight.source_service}</span>
                        )}
                      </div>
                      <h3 className="font-semibold text-gray-900">{insight.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{insight.summary}</p>
                      {insight.patient_name && (
                        <p className="text-xs text-gray-400 mt-1">Patient: {insight.patient_name}</p>
                      )}
                    </div>
                    <div className="ml-4 flex flex-col items-end space-y-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        insight.is_reviewed ? "bg-blue-100 text-blue-700" : "bg-orange-100 text-orange-700"
                      }`}>
                        {insight.is_reviewed ? "Reviewed" : "Pending"}
                      </span>
                      <span className="text-xs text-gray-400">{new Date(insight.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                  {insight.is_reviewed && insight.clinical_action_taken && (
                    <div className="mt-2 p-2 bg-white rounded text-sm text-gray-600">
                      <span className="font-medium">Action: </span>{insight.clinical_action_taken}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
