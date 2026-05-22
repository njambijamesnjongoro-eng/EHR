"use client";

import { useEffect, useState } from "react";
import { populationHealthApi } from "@/lib/api/populationHealth";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { PopulationHealthInsight, PredictiveForecast } from "@/lib/types";

export default function PopulationHealthPage() {
  const [insights, setInsights] = useState<PopulationHealthInsight[]>([]);
  const [forecasts, setForecasts] = useState<PredictiveForecast[]>([]);
  const [diseaseBurden, setDiseaseBurden] = useState<Record<string, unknown> | null>(null);
  const [healthcareAccess, setHealthcareAccess] = useState<Record<string, unknown> | null>(null);
  const [healthEquity, setHealthEquity] = useState<Record<string, unknown> | null>(null);
  const [regionalData, setRegionalData] = useState<Record<string, unknown> | null>(null);
  const [regions, setRegions] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"insights" | "forecasts" | "burden" | "access" | "equity" | "regional">("insights");

  useEffect(() => {
    loadInitial();
  }, []);

  async function loadInitial() {
    setLoading(true);
    try {
      const [insightRes, forecastRes, burdenRes] = await Promise.all([
        populationHealthApi.listInsights({ limit: 20 }),
        populationHealthApi.listForecasts({ limit: 20 }),
        populationHealthApi.diseaseBurden(),
      ]);
      setInsights((insightRes.results ?? insightRes.data ?? []) as PopulationHealthInsight[]);
      setForecasts((forecastRes.results ?? forecastRes.data ?? []) as PredictiveForecast[]);
      if (burdenRes.data) setDiseaseBurden(burdenRes.data as Record<string, unknown>);
    } catch (e) {
      console.error("Failed to load population health data", e);
    } finally {
      setLoading(false);
    }
  }

  async function loadAccess() {
    try {
      const res = await populationHealthApi.healthcareAccess();
      if (res.data) setHealthcareAccess(res.data as Record<string, unknown>);
      setActiveTab("access");
    } catch (e) {
      console.error("Failed to load healthcare access", e);
    }
  }

  async function loadEquity() {
    try {
      const res = await populationHealthApi.healthEquity();
      if (res.data) setHealthEquity(res.data as Record<string, unknown>);
      setActiveTab("equity");
    } catch (e) {
      console.error("Failed to load health equity", e);
    }
  }

  async function loadRegional() {
    if (!regions) return;
    try {
      const res = await populationHealthApi.regionalComparison(regions);
      if (res.data) setRegionalData(res.data as Record<string, unknown>);
      setActiveTab("regional");
    } catch (e) {
      console.error("Failed to load regional comparison", e);
    }
  }

  const tabs = [
    { key: "insights" as const, label: "Health Insights" },
    { key: "forecasts" as const, label: "Predictive Forecasts" },
    { key: "burden" as const, label: "Disease Burden" },
    { key: "access" as const, label: "Healthcare Access" },
    { key: "equity" as const, label: "Health Equity" },
    { key: "regional" as const, label: "Regional Comparison" },
  ];

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Population Health Analytics</h1>
        <p className="text-sm text-gray-500 mt-1">Nationwide population health insights, disease surveillance, and predictive analytics</p>
      </div>

      <div className="flex space-x-1 border-b border-gray-200">
        {tabs.map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === tab.key ? "border-primary-600 text-primary-700" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "insights" && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Population Health Insights ({insights.length})</h2>
          {insights.length === 0 ? (
            <p className="text-sm text-gray-500">No insights available</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="pb-2 pr-4 font-medium">Indicator</th>
                    <th className="pb-2 pr-4 font-medium">County</th>
                    <th className="pb-2 pr-4 font-medium">Sub County</th>
                    <th className="pb-2 pr-4 font-medium">Value</th>
                    <th className="pb-2 pr-4 font-medium">Population</th>
                    <th className="pb-2 pr-4 font-medium">Trend</th>
                    <th className="pb-2 pr-4 font-medium">Period</th>
                  </tr>
                </thead>
                <tbody>
                  {insights.map((insight) => (
                    <tr key={insight.id} className="border-b border-gray-100">
                      <td className="py-2 pr-4 font-medium text-gray-900">{insight.indicator_name}</td>
                      <td className="py-2 pr-4 text-gray-600">{insight.county}</td>
                      <td className="py-2 pr-4 text-gray-600">{insight.sub_county}</td>
                      <td className="py-2 pr-4">{insight.indicator_value?.toLocaleString()}</td>
                      <td className="py-2 pr-4 text-gray-600">{insight.population_base?.toLocaleString()}</td>
                      <td className="py-2 pr-4">
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          insight.trend_direction === "up" ? "bg-red-100 text-red-700" :
                          insight.trend_direction === "down" ? "bg-green-100 text-green-700" :
                          "bg-gray-100 text-gray-600"
                        }`}>{insight.trend_direction}</span>
                      </td>
                      <td className="py-2 pr-4 text-gray-500 text-xs">{new Date(insight.period_start).toLocaleDateString()} — {new Date(insight.period_end).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === "forecasts" && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Predictive Forecasts ({forecasts.length})</h2>
          {forecasts.length === 0 ? (
            <p className="text-sm text-gray-500">No forecasts available</p>
          ) : (
            <div className="space-y-3">
              {forecasts.map((f) => (
                <div key={f.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-xs font-medium text-gray-500 uppercase">{f.domain}</span>
                        <span className="text-xs text-gray-400">Model: {f.model_name}</span>
                      </div>
                      <h3 className="font-semibold text-gray-900">{f.metric_name}</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Predicted: <span className="font-bold">{f.predicted_value?.toLocaleString()}</span>
                        {f.actual_value !== null && <> | Actual: <span className="font-bold">{f.actual_value?.toLocaleString()}</span></>}
                        {f.predicted_lower !== null && f.predicted_upper !== null && (
                          <> | Range: {f.predicted_lower?.toLocaleString()} — {f.predicted_upper?.toLocaleString()}</>
                        )}
                      </p>
                      <div className="flex items-center space-x-3 mt-2 text-xs text-gray-500">
                        <span>County: {f.county}</span>
                        <span>Region: {f.region}</span>
                        <span>Forecast: {new Date(f.forecast_date).toLocaleDateString()}</span>
                        <span className={`px-1.5 py-0.5 rounded-full ${
                          f.trend_direction === "up" ? "bg-red-100 text-red-700" :
                          f.trend_direction === "down" ? "bg-green-100 text-green-700" :
                          "bg-gray-100 text-gray-600"
                        }`}>{f.trend_direction}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "burden" && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Disease Burden Analysis</h2>
          {diseaseBurden ? (
            <pre className="text-sm text-gray-600 bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
              {JSON.stringify(diseaseBurden, null, 2)}
            </pre>
          ) : (
            <p className="text-sm text-gray-500">No disease burden data available</p>
          )}
        </div>
      )}

      {activeTab === "access" && (
        <div>
          {!healthcareAccess ? (
            <div className="card">
              <button onClick={loadAccess} className="btn btn-primary">Load Healthcare Access Data</button>
            </div>
          ) : (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Healthcare Access Metrics</h2>
              <pre className="text-sm text-gray-600 bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
                {JSON.stringify(healthcareAccess, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {activeTab === "equity" && (
        <div>
          {!healthEquity ? (
            <div className="card">
              <button onClick={loadEquity} className="btn btn-primary">Load Health Equity Data</button>
            </div>
          ) : (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Health Equity Analysis</h2>
              <pre className="text-sm text-gray-600 bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
                {JSON.stringify(healthEquity, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {activeTab === "regional" && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Regional Comparison</h2>
          <div className="flex items-end space-x-3 mb-4">
            <div className="flex-1">
              <label className="label">Regions (comma-separated)</label>
              <input type="text" value={regions} onChange={(e) => setRegions(e.target.value)} className="input" placeholder="e.g. Nairobi, Mombasa, Kisumu" />
            </div>
            <button onClick={loadRegional} disabled={!regions} className="btn btn-primary">Compare</button>
          </div>
          {regionalData && (
            <pre className="text-sm text-gray-600 bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
              {JSON.stringify(regionalData, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
