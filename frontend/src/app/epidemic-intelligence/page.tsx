"use client";

import { useEffect, useState } from "react";
import { epidemicApi } from "@/lib/api/epidemic";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { EpidemicAlert, RegionalSpread, PublicHealthForecast } from "@/lib/types";

export default function EpidemicIntelligencePage() {
  const [alerts, setAlerts] = useState<EpidemicAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [spread, setSpread] = useState<RegionalSpread | null>(null);
  const [forecastResult, setForecastResult] = useState<PublicHealthForecast | null>(null);
  const [diseaseCode, setDiseaseCode] = useState("");
  const [county, setCounty] = useState("");

  useEffect(() => {
    loadAlerts();
  }, []);

  async function loadAlerts() {
    setLoading(true);
    try {
      const res = await epidemicApi.listAlerts({ is_active: "true" });
      setAlerts((res.results ?? res.data ?? []) as EpidemicAlert[]);
    } catch (e) {
      console.error("Failed to load alerts", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleDetectOutbreak() {
    setDetecting(true);
    try {
      const res = await epidemicApi.detectOutbreak(7);
      const newAlerts = (res.results ?? res.data ?? []) as EpidemicAlert[];
      setAlerts((prev) => [...newAlerts, ...prev]);
    } catch (e) {
      console.error("Failed to detect outbreak", e);
    } finally {
      setDetecting(false);
    }
  }

  async function handleRegionalSpread() {
    if (!diseaseCode) return;
    try {
      const res = await epidemicApi.regionalSpread(diseaseCode, 30);
      if (res.data) setSpread(res.data);
    } catch (e) {
      console.error("Failed to load regional spread", e);
    }
  }

  async function handleForecast() {
    if (!diseaseCode) return;
    try {
      const res = await epidemicApi.forecast(diseaseCode, county || undefined, 14);
      if (res.data) setForecastResult(res.data);
    } catch (e) {
      console.error("Failed to generate forecast", e);
    }
  }

  const levelColors: Record<string, string> = {
    green: "bg-green-100 text-green-800 border-green-300",
    yellow: "bg-yellow-100 text-yellow-800 border-yellow-300",
    orange: "bg-orange-100 text-orange-800 border-orange-300",
    red: "bg-red-100 text-red-800 border-red-300",
    critical: "bg-red-200 text-red-900 border-red-400",
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Epidemic Intelligence</h1>
        <p className="text-sm text-gray-500 mt-1">Real-time outbreak detection, regional spread, and disease forecasting</p>
      </div>

      <div className="flex items-center space-x-3">
        <button onClick={handleDetectOutbreak} disabled={detecting} className="btn btn-primary">
          {detecting ? "Scanning..." : "Detect Outbreak Patterns"}
        </button>
      </div>

      {loading ? <LoadingSpinner /> : (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Active Alerts ({alerts.length})</h2>
          {alerts.length === 0 ? (
            <div className="card">
              <p className="text-gray-500 text-sm">No active epidemic alerts</p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div key={alert.id} className={`card border-l-4 ${levelColors[alert.alert_level]?.split(" ")[2] || "border-gray-300"}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${levelColors[alert.alert_level] || "bg-gray-100"}`}>
                        {alert.alert_level_display}
                      </span>
                      <span className="text-xs font-medium text-gray-500">{alert.alert_source_display}</span>
                      {alert.is_active && (
                        <span className="text-xs text-green-600 font-medium">ACTIVE</span>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-900">{alert.disease_name} ({alert.disease_code})</h3>
                    <p className="text-sm text-gray-600 mt-1">{alert.county}{alert.sub_county ? ` - ${alert.sub_county}` : ""}</p>
                    <div className="grid grid-cols-4 gap-4 mt-2">
                      <div><span className="text-xs text-gray-500">Confirmed</span><p className="font-semibold">{alert.confirmed_cases}</p></div>
                      <div><span className="text-xs text-gray-500">Suspected</span><p className="font-semibold">{alert.suspected_cases}</p></div>
                      <div><span className="text-xs text-gray-500">Deaths</span><p className="font-semibold text-red-600">{alert.reported_deaths}</p></div>
                      <div><span className="text-xs text-gray-500">Attack Rate</span><p className="font-semibold">{alert.attack_rate}</p></div>
                    </div>
                    {alert.recommended_actions && (
                      <p className="text-xs text-gray-600 mt-2"><span className="font-medium">Actions:</span> {alert.recommended_actions}</p>
                    )}
                  </div>
                  <div className="ml-4 text-right">
                    <p className="text-xs text-gray-400">{new Date(alert.detected_at).toLocaleString()}</p>
                    {alert.doubling_time_days && (
                      <p className="text-xs text-orange-600 mt-1">Doubling: {alert.doubling_time_days}d</p>
                    )}
                    {alert.r0_estimate && (
                      <p className="text-xs text-purple-600">R0: {alert.r0_estimate}</p>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Regional Spread</h2>
          <div className="flex items-center space-x-2 mb-4">
            <input value={diseaseCode} onChange={(e) => setDiseaseCode(e.target.value)} className="input flex-1" placeholder="Disease code (e.g. ICD-10)" />
            <button onClick={handleRegionalSpread} className="btn btn-secondary">Load</button>
          </div>
          {spread && (
            <div className="space-y-2">
              <p className="text-sm text-gray-600">Total cases: <span className="font-semibold">{spread.total_cases}</span> across {spread.affected_counties} counties</p>
              <p className="text-sm text-gray-600">Pattern: <span className="font-semibold">{spread.spread_pattern}</span></p>
              <div className="space-y-1 mt-2">
                {spread.county_breakdown.map((c) => (
                  <div key={c.county} className="flex justify-between text-sm">
                    <span>{c.county}</span>
                    <span className="font-semibold">{c.cases}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Disease Forecast</h2>
          <div className="flex items-center space-x-2 mb-4">
            <input value={diseaseCode} onChange={(e) => setDiseaseCode(e.target.value)} className="input flex-1" placeholder="Disease code" />
            <input value={county} onChange={(e) => setCounty(e.target.value)} className="input w-32" placeholder="County" />
            <button onClick={handleForecast} className="btn btn-secondary">Forecast</button>
          </div>
          {forecastResult && (
            <div className="space-y-2">
              <p className="text-sm text-gray-600">{forecastResult.disease_name} - {forecastResult.forecast_date}</p>
              <p className="text-lg font-bold text-gray-900">{forecastResult.predicted_cases} predicted cases</p>
              {forecastResult.predicted_lower !== null && (
                <p className="text-xs text-gray-500">Range: {forecastResult.predicted_lower} - {forecastResult.predicted_upper}</p>
              )}
              <p className="text-sm">Trend: <span className="font-semibold">{forecastResult.trend_direction}</span></p>
              <p className="text-sm">Risk: <span className="font-semibold">{forecastResult.risk_level}</span></p>
              <p className="text-xs text-gray-400">Model: {forecastResult.model_name}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
