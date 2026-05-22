"use client";

import { useEffect, useState } from "react";
import { timelineApi } from "@/lib/api/timeline";
import LoadingSpinner from "@/components/ui/loading-spinner";
import type { TimelineEvent, Patient } from "@/lib/types";

interface TimelineTabProps {
  patient: Patient;
}

const typeIcons: Record<string, string> = {
  visit: "🩺",
  diagnosis: "📋",
  prescription: "💊",
  lab_request: "🔬",
  lab_result: "📊",
};

const typeColors: Record<string, string> = {
  visit: "border-l-blue-500",
  diagnosis: "border-l-red-500",
  prescription: "border-l-purple-500",
  lab_request: "border-l-amber-500",
  lab_result: "border-l-green-500",
};

export default function TimelineTab({ patient }: TimelineTabProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    timelineApi
      .getPatientTimeline(patient.id)
      .then((res) => {
        setEvents(res.data || []);
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, [patient.id]);

  if (isLoading) return <LoadingSpinner />;

  if (events.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No medical history events found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900">Patient Medical Timeline</h3>
      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
        <div className="space-y-4">
          {events.map((event, idx) => (
            <div key={`${event.type}-${event.id}-${idx}`} className="relative pl-10">
              <div className={`absolute left-2.5 w-3 h-3 rounded-full bg-white border-2 border-gray-300 -translate-x-1/2 mt-1.5 ${
                event.type === "visit" ? "bg-blue-500 border-blue-500" :
                event.type === "diagnosis" ? "bg-red-500 border-red-500" :
                event.type === "prescription" ? "bg-purple-500 border-purple-500" :
                event.type === "lab_request" ? "bg-amber-500 border-amber-500" :
                event.type === "lab_result" ? "bg-green-500 border-green-500" : ""
              }`} />
              <div className={`border border-gray-200 rounded-lg p-4 border-l-4 ${typeColors[event.type] || "border-l-gray-300"}`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-base">{typeIcons[event.type] || "📄"}</span>
                    <span className={`badge ${
                      event.type === "visit" ? "badge-info" :
                      event.type === "diagnosis" ? "badge-danger" :
                      event.type === "prescription" ? "badge-warning" :
                      event.type === "lab_request" ? "badge-warning" :
                      event.type === "lab_result" ? "badge-success" : ""
                    }`}>
                      {event.type.replace("_", " ")}
                    </span>
                    <h4 className="font-medium text-gray-900">{event.title}</h4>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(event.date).toLocaleDateString("en-US", {
                      year: "numeric", month: "short", day: "numeric",
                      hour: "2-digit", minute: "2-digit",
                    })}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-2">{event.description}</p>
                {event.extra && Object.keys(event.extra).length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {Object.entries(event.extra).map(([key, val]) => (
                      <span key={key} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                        {key.replace("_", " ")}: {String(val)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
