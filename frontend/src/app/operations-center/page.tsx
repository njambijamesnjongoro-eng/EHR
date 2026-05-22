"use client";

import { useEffect, useState } from "react";
import { healthDataFabricApi } from "@/lib/api/healthDataFabric";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { InfrastructureEvent, EventChainItem, CorrelatedEvents } from "@/lib/types";

export default function OperationsCenterPage() {
  const [infraEvents, setInfraEvents] = useState<InfrastructureEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"infra" | "stream" | "chain" | "correlate" | "errors">("infra");
  const [correlationId, setCorrelationId] = useState("");
  const [chainItems, setChainItems] = useState<EventChainItem[]>([]);
  const [aggregateType, setAggregateType] = useState("");
  const [aggregateId, setAggregateId] = useState("");
  const [correlatedData, setCorrelatedData] = useState<CorrelatedEvents | null>(null);
  const [errorEvents, setErrorEvents] = useState<InfrastructureEvent[]>([]);
  const [recentErrors, setRecentErrors] = useState(false);

  useEffect(() => {
    loadInfra();
  }, []);

  async function loadInfra() {
    setLoading(true);
    try {
      const res = await healthDataFabricApi.listInfrastructure();
      setInfraEvents((res.results ?? res.data ?? []) as InfrastructureEvent[]);
    } catch (e) {
      console.error("Failed to load infrastructure events", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleEventChain() {
    if (!correlationId) return;
    try {
      const res = await healthDataFabricApi.eventChain(correlationId);
      setChainItems((res.results ?? res.data ?? []) as EventChainItem[]);
    } catch (e) {
      console.error("Failed to load event chain", e);
    }
  }

  async function handleCorrelate() {
    if (!aggregateType || !aggregateId) return;
    try {
      const res = await healthDataFabricApi.correlateEvents(aggregateType, aggregateId);
      if (res.data) setCorrelatedData(res.data);
    } catch (e) {
      console.error("Failed to correlate events", e);
    }
  }

  async function handleLoadErrors() {
    setRecentErrors(true);
    setLoading(true);
    try {
      const res = await healthDataFabricApi.recentErrors(24);
      setErrorEvents((res.results ?? res.data ?? []) as InfrastructureEvent[]);
    } catch (e) {
      console.error("Failed to load recent errors", e);
    } finally {
      setLoading(false);
    }
  }

  const tabs = [
    { key: "infra" as const, label: "Infrastructure Events" },
    { key: "chain" as const, label: "Event Chain" },
    { key: "correlate" as const, label: "Correlation" },
    { key: "errors" as const, label: "Recent Errors" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Operations Center</h1>
        <p className="text-sm text-gray-500 mt-1">Infrastructure monitoring, event streams, and system-wide operations</p>
      </div>

      <div className="flex space-x-1 border-b border-gray-200">
        {tabs.map((tab) => (
          <button key={tab.key} onClick={() => {
            setActiveTab(tab.key);
            if (tab.key === "errors") handleLoadErrors();
            if (tab.key === "infra") loadInfra();
          }} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === tab.key ? "border-primary-600 text-primary-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "infra" && (
        <div>
          {loading ? <LoadingSpinner /> : infraEvents.length === 0 ? (
            <div className="card"><p className="text-gray-500 text-sm">No infrastructure events</p></div>
          ) : (
            <div className="space-y-3">
              {infraEvents.map((ev) => {
                const sevColors: Record<string, string> = {
                  info: "border-blue-200 bg-blue-50",
                  warning: "border-yellow-200 bg-yellow-50",
                  error: "border-red-200 bg-red-50",
                  critical: "border-red-300 bg-red-100",
                };
                return (
                  <div key={ev.id} className={`card border-l-4 ${sevColors[ev.severity] || "border-gray-200"}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-xs font-medium text-gray-500 uppercase">{ev.event_type.replace(/_/g, " ")}</span>
                          <span className="text-xs text-gray-400">{ev.service_name}</span>
                          <span className="text-xs text-gray-400">{ev.host_name}</span>
                        </div>
                        <p className="text-sm font-medium text-gray-900">{ev.message}</p>
                        {ev.auto_action_taken && (
                          <p className="text-xs text-gray-600 mt-1">Auto-action: {ev.auto_action_taken} {ev.auto_action_success !== null && (ev.auto_action_success ? "✓" : "✗")}</p>
                        )}
                      </div>
                      <div className="ml-4 text-right">
                        <p className="text-xs text-gray-400">{new Date(ev.occurred_at).toLocaleString()}</p>
                        <span className={`text-xs font-medium ${ev.resolved ? "text-green-600" : "text-orange-600"}`}>
                          {ev.resolved ? "Resolved" : "Active"}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {activeTab === "chain" && (
        <div className="space-y-4">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Event Chain Viewer</h2>
            <div className="flex items-center space-x-2">
              <input value={correlationId} onChange={(e) => setCorrelationId(e.target.value)} className="input flex-1" placeholder="Correlation ID" />
              <button onClick={handleEventChain} className="btn btn-primary">View Chain</button>
            </div>
          </div>
          {chainItems.length > 0 && (
            <div className="space-y-2">
              {chainItems.map((item, i) => (
                <div key={item.event_id} className="card flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold">
                    {i + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{item.type}</p>
                    <p className="text-xs text-gray-500">Source: {item.source}</p>
                    <p className="text-xs text-gray-400">Event ID: {item.event_id}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400">{new Date(item.occurred_at).toLocaleString()}</p>
                    {item.duration_from_previous_s !== null && (
                      <p className="text-xs text-gray-500">+{item.duration_from_previous_s}s</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "correlate" && (
        <div className="space-y-4">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Event Correlation</h2>
            <div className="flex items-center space-x-2">
              <input value={aggregateType} onChange={(e) => setAggregateType(e.target.value)} className="input w-40" placeholder="Type (e.g. visit)" />
              <input value={aggregateId} onChange={(e) => setAggregateId(e.target.value)} className="input flex-1" placeholder="Aggregate ID" />
              <button onClick={handleCorrelate} className="btn btn-primary">Correlate</button>
            </div>
          </div>
          {correlatedData && (
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-2">{correlatedData.aggregate_type} #{correlatedData.aggregate_id}</h3>
              <p className="text-sm text-gray-600 mb-3">{correlatedData.total_events} total events</p>
              <div className="space-y-2">
                {correlatedData.timeline.map((t, i) => (
                  <div key={t.event_id} className="flex items-start space-x-2">
                    <div className="w-2 h-2 rounded-full bg-primary-500 mt-1.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">{t.summary}</p>
                      <p className="text-xs text-gray-500">{t.source} - {t.type}</p>
                    </div>
                    <p className="text-xs text-gray-400">{new Date(t.time).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "errors" && (
        <div>
          {recentErrors && loading ? <LoadingSpinner /> : errorEvents.length === 0 ? (
            <div className="card"><p className="text-gray-500 text-sm">No recent errors in the last 24 hours</p></div>
          ) : (
            <div className="space-y-3">
              {errorEvents.map((ev) => (
                <div key={ev.id} className="card border-red-200 bg-red-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-xs font-medium text-gray-500 uppercase">{ev.event_type}</span>
                        <span className="text-xs text-gray-400">{ev.service_name}</span>
                      </div>
                      <p className="text-sm font-medium text-gray-900">{ev.message}</p>
                      {ev.host_name && <p className="text-xs text-gray-500">Host: {ev.host_name}</p>}
                    </div>
                    <div className="ml-4 text-right">
                      <p className="text-xs text-gray-400">{new Date(ev.occurred_at).toLocaleString()}</p>
                      <span className="text-xs font-medium text-red-600 capitalize">{ev.severity}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
