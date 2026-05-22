from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import ExternalSystem, EnterpriseAuditEvent, EventStreamLog
from events.event_bus import EventBus


class EnhancedInteroperabilityService:
    """Advanced interoperability for FHIR, insurance, government, and external systems."""

    FHIR_RESOURCE_TYPES = [
        "Patient", "Encounter", "Observation", "MedicationRequest",
        "DiagnosticReport", "Immunization", "Condition", "Procedure",
        "CarePlan", "DocumentReference",
    ]

    @staticmethod
    def get_system_connection_status(system_id: int) -> dict:
        try:
            system = ExternalSystem.objects.get(id=system_id)
        except ExternalSystem.DoesNotExist:
            return {"error": "System not found"}

        recent_events = EventStreamLog.objects.filter(
            event_source="integration",
            aggregate_id=str(system.id),
            occurred_at__gte=timezone.now() - timedelta(hours=24),
        ).order_by("-occurred_at")[:20]

        return {
            "system_id": system.id,
            "system_name": system.system_name,
            "system_type": system.system_type,
            "is_active": system.is_active,
            "auth_type": system.auth_type,
            "last_sync_at": system.last_sync_at.isoformat() if system.last_sync_at else None,
            "last_sync_status": system.last_sync_status,
            "recent_events_count": recent_events.count(),
            "health_status": "healthy" if system.is_active else "inactive",
        }

    @staticmethod
    def get_supported_fhir_resources() -> list:
        return EnhancedInteroperabilityService.FHIR_RESOURCE_TYPES

    @staticmethod
    def map_fhir_resource(resource_type: str, internal_data: dict) -> dict:
        from services.interop_service import InteroperabilityService
        return InteroperabilityService.convert_to_fhir(resource_type, internal_data)

    @staticmethod
    def check_external_system_health() -> list:
        systems = ExternalSystem.objects.filter(is_active=True)
        results = []

        for system in systems:
            status = "unknown"
            if system.last_sync_status == "success":
                if system.last_sync_at and system.last_sync_at >= timezone.now() - timedelta(hours=24):
                    status = "healthy"
                else:
                    status = "stale"
            elif system.last_sync_status == "error":
                status = "error"

            results.append({
                "id": system.id,
                "name": system.system_name,
                "type": system.system_type,
                "status": status,
                "last_sync": system.last_sync_at.isoformat() if system.last_sync_at else None,
            })

        return results

    @staticmethod
    def log_integration_event(system_id: int, action: str, status: str, data: dict = None):
        try:
            system = ExternalSystem.objects.get(id=system_id)
        except ExternalSystem.DoesNotExist:
            return None

        system.last_sync_at = timezone.now()
        system.last_sync_status = status
        system.save(update_fields=["last_sync_at", "last_sync_status"])

        EnterpriseAuditEvent.objects.create(
            event_type=EnterpriseAuditEvent.EventType.INTEGRATION,
            action=action,
            resource_type="ExternalSystem",
            resource_id=str(system.id),
            description=f"Integration {action} for {system.system_name}: {status}",
            metadata=data or {},
            severity="error" if status == "error" else "info",
        )

        EventBus.emit_integration(
            event_type=f"integration.{action}",
            data={
                "system_id": system.id,
                "system_name": system.system_name,
                "action": action,
                "status": status,
                **(data or {}),
            },
            aggregate_type="ExternalSystem",
            aggregate_id=str(system.id),
        )

    @staticmethod
    def get_integration_log(system_id: int = None, limit: int = 100):
        qs = EnterpriseAuditEvent.objects.filter(
            event_type=EnterpriseAuditEvent.EventType.INTEGRATION,
        )
        if system_id:
            qs = qs.filter(resource_id=str(system_id))
        return qs.order_by("-created_at")[:limit]
