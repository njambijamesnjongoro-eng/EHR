import json
import uuid
from datetime import datetime, timezone

from django.db import transaction

from core.models import EventStreamLog, EnterpriseAuditEvent


class EventBus:
    """Domain event bus for healthcare event-driven architecture.

    Events are persisted to EventStreamLog and can be forwarded to:
    - Kafka (future)
    - Celery tasks
    - WebSocket channels
    - External webhooks
    """

    @staticmethod
    def emit(
        event_source: str,
        event_type: str,
        data: dict,
        *,
        aggregate_type: str = "",
        aggregate_id: str = "",
        correlation_id: str = "",
        causation_id: str = "",
        metadata: dict = None,
        event_version: str = "1.0",
    ) -> EventStreamLog:
        event_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)

        log_entry = EventStreamLog.objects.create(
            event_id=event_id,
            event_source=event_source,
            event_type=event_type,
            event_version=event_version,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            data=data,
            metadata=metadata or {},
            correlation_id=correlation_id or event_id,
            causation_id=causation_id,
            occurred_at=now,
        )

        return log_entry

    @staticmethod
    def emit_clinical(data: dict, event_type: str, **kwargs):
        return EventBus.emit("clinical", event_type, data, **kwargs)

    @staticmethod
    def emit_wearable(data: dict, event_type: str, **kwargs):
        return EventBus.emit("wearable", event_type, data, **kwargs)

    @staticmethod
    def emit_security(data: dict, event_type: str, **kwargs):
        return EventBus.emit("security", event_type, data, **kwargs)

    @staticmethod
    def emit_system(data: dict, event_type: str, **kwargs):
        return EventBus.emit("system", event_type, data, **kwargs)

    @staticmethod
    def emit_integration(data: dict, event_type: str, **kwargs):
        return EventBus.emit("integration", event_type, data, **kwargs)

    @staticmethod
    def emit_ai(data: dict, event_type: str, **kwargs):
        return EventBus.emit("ai", event_type, data, **kwargs)

    @staticmethod
    def get_events_by_aggregate(aggregate_type: str, aggregate_id: str, limit: int = 100):
        return EventStreamLog.objects.filter(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
        ).order_by("-occurred_at")[:limit]

    @staticmethod
    def get_events_by_correlation(correlation_id: str, limit: int = 100):
        return EventStreamLog.objects.filter(
            correlation_id=correlation_id,
        ).order_by("-occurred_at")[:limit]

    @staticmethod
    def get_events_by_source(event_source: str, event_type: str = None, limit: int = 100):
        qs = EventStreamLog.objects.filter(event_source=event_source)
        if event_type:
            qs = qs.filter(event_type=event_type)
        return qs.order_by("-occurred_at")[:limit]
