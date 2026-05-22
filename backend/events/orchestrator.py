from datetime import timedelta
from collections import defaultdict

from django.db import transaction
from django.utils import timezone

from core.models import EventStreamLog, InfrastructureEvent, EnterpriseAuditEvent


class EventOrchestrator:
    """Distributed event orchestration: routing, correlation, retry, and infrastructure event processing."""

    ROUTING_RULES = {
        "clinical": ["ai_assist", "analytics", "audit"],
        "wearable": ["analytics", "monitoring", "ai_assist"],
        "security": ["monitoring", "audit", "ai_assist"],
        "system": ["monitoring", "infrastructure", "audit"],
        "integration": ["monitoring", "audit", "sync"],
        "ai": ["analytics", "audit", "monitoring"],
    }

    @staticmethod
    @transaction.atomic
    def process_event(event: EventStreamLog):
        routes = EventOrchestrator.ROUTING_RULES.get(event.event_source, ["audit"])
        event.metadata["routed_to"] = routes
        event.save(update_fields=["metadata"])

        if event.event_source in ("system", "infrastructure"):
            EventOrchestrator._create_infrastructure_event(event)

        return routes

    @staticmethod
    def get_event_chain(correlation_id: str) -> list:
        events = EventStreamLog.objects.filter(correlation_id=correlation_id).order_by("occurred_at")
        chain = []
        for event in events:
            duration = None
            if chain:
                duration = (event.occurred_at - chain[-1]["occurred_at"]).total_seconds()
            chain.append({
                "event_id": event.event_id,
                "source": event.event_source,
                "type": event.event_type,
                "occurred_at": event.occurred_at.isoformat(),
                "duration_from_previous_s": duration,
            })
        return chain

    @staticmethod
    def count_events_by_source(hours: int = 24) -> dict:
        since = timezone.now() - timedelta(hours=hours)
        counts = defaultdict(int)
        for event in EventStreamLog.objects.filter(occurred_at__gte=since).values("event_source").annotate(
            count=__import__("django.db.models", fromlist=["Count"]).Count("id")
        ):
            counts[event["event_source"]] = event["count"]
        return dict(counts)

    @staticmethod
    def _create_infrastructure_event(event: EventStreamLog):
        InfrastructureEvent.objects.create(
            event_type=InfrastructureEvent.EventType.HEALTH_CHECK,
            severity="info",
            service_name=event.event_source,
            message=f"Event processed: {event.event_type}",
            metric_data={"event_id": event.event_id, "event_type": event.event_type},
            occurred_at=event.occurred_at,
        )

    @staticmethod
    def correlate_events(aggregate_type: str, aggregate_id: str) -> dict:
        events = EventStreamLog.objects.filter(
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
        ).order_by("occurred_at")

        return {
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "total_events": events.count(),
            "timeline": [
                {
                    "event_id": e.event_id,
                    "source": e.event_source,
                    "type": e.event_type,
                    "time": e.occurred_at.isoformat(),
                    "summary": str(e.data)[:200],
                }
                for e in events
            ],
        }

    @staticmethod
    def get_recent_errors(hours: int = 1) -> list:
        since = timezone.now() - timedelta(hours=hours)
        return list(InfrastructureEvent.objects.filter(
            occurred_at__gte=since, severity__in=["error", "critical"],
        ).order_by("-occurred_at")[:20])
