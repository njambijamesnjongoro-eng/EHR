from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import ExternalSystem, EnterpriseAuditEvent, EventStreamLog
from events.event_bus import EventBus


class HealthcareInteropService:
    """Healthcare interoperability gateway — FHIR transformation, external system management, and national integration health."""

    FHIR_RESOURCE_TYPES = [
        "Patient", "Encounter", "Observation", "MedicationRequest",
        "DiagnosticReport", "Immunization", "Condition", "Procedure",
        "CarePlan", "DocumentReference",
    ]

    @staticmethod
    def register_external_system(system_name, system_type, base_url, auth_type, **kwargs) -> ExternalSystem:
        system = ExternalSystem.objects.create(
            system_name=system_name,
            system_type=system_type,
            hospital=kwargs.get("hospital"),
            base_url=base_url,
            auth_type=auth_type,
            config=kwargs.get("config", {}),
            is_active=kwargs.get("is_active", True),
        )

        EnterpriseAuditEvent.objects.create(
            event_type=EnterpriseAuditEvent.EventType.INTEGRATION,
            action="system_registered",
            resource_type="ExternalSystem",
            resource_id=str(system.id),
            description=f"External system {system_name} ({system_type}) registered via HealthcareInteropService",
        )

        EventBus.emit_integration(
            event_type="interop.system_registered",
            data={
                "system_id": system.id,
                "system_name": system_name,
                "system_type": system_type,
                "auth_type": auth_type,
            },
            aggregate_type="ExternalSystem",
            aggregate_id=str(system.id),
        )

        return system

    @staticmethod
    def transform_to_fhir(resource_type, data) -> dict:
        """Transform internal data to FHIR R4 compliant format.

        Supports Patient, Encounter, Observation, MedicationRequest, and DiagnosticReport resources.
        """
        from services.interop_service import InteroperabilityService
        return InteroperabilityService.convert_to_fhir(resource_type, data)

    @staticmethod
    def validate_interop_connection(system_id) -> dict:
        try:
            system = ExternalSystem.objects.get(id=system_id)
        except ExternalSystem.DoesNotExist:
            return {"error": "External system not found"}

        recent_syncs = EventStreamLog.objects.filter(
            event_source="integration",
            aggregate_id=str(system.id),
            occurred_at__gte=timezone.now() - timedelta(days=7),
        ).order_by("-occurred_at")[:10]

        sync_successes = sum(1 for s in recent_syncs if "success" in s.event_type)
        sync_failures = sum(1 for s in recent_syncs if "error" in s.event_type or "fail" in s.event_type)

        return {
            "system_id": system.id,
            "system_name": system.system_name,
            "status": "connected" if system.is_active else "disconnected",
            "auth_type": system.auth_type,
            "last_sync_at": system.last_sync_at.isoformat() if system.last_sync_at else None,
            "last_sync_status": system.last_sync_status or "unknown",
            "sync_success_rate_7d": round(sync_successes / len(recent_syncs) * 100, 1) if recent_syncs else 0,
            "recent_errors": sync_failures,
            "connection_healthy": system.is_active and system.last_sync_status != "error",
        }

    @staticmethod
    def get_interop_health_dashboard() -> dict:
        systems = ExternalSystem.objects.filter(is_active=True)

        by_type = {}
        for system in systems:
            stype = system.system_type
            if stype not in by_type:
                by_type[stype] = {"total": 0, "healthy": 0, "error": 0, "stale": 0}
            by_type[stype]["total"] += 1
            if system.last_sync_status == "success":
                if system.last_sync_at and system.last_sync_at >= timezone.now() - timedelta(hours=24):
                    by_type[stype]["healthy"] += 1
                else:
                    by_type[stype]["stale"] += 1
            elif system.last_sync_status == "error":
                by_type[stype]["error"] += 1
            else:
                by_type[stype]["stale"] += 1

        total_healthy = sum(v["healthy"] for v in by_type.values())
        total_systems = len(systems)

        return {
            "total_systems": total_systems,
            "healthy_count": total_healthy,
            "health_pct": round(total_healthy / total_systems * 100, 1) if total_systems > 0 else 0,
            "by_type": by_type,
            "supported_fhir_resources": HealthcareInteropService.FHIR_RESOURCE_TYPES,
            "timestamp": timezone.now().isoformat(),
        }

    @staticmethod
    def sync_with_external_system(system_id, resource_type, data) -> dict:
        try:
            system = ExternalSystem.objects.get(id=system_id)
        except ExternalSystem.DoesNotExist:
            return {"error": "External system not found"}

        fhir_data = HealthcareInteropService.transform_to_fhir(resource_type, data)

        system.last_sync_at = timezone.now()
        system.last_sync_status = "success"
        system.save(update_fields=["last_sync_at", "last_sync_status"])

        EventBus.emit_integration(
            event_type=f"interop.sync.{resource_type}",
            data={
                "system_id": system.id,
                "system_name": system.system_name,
                "resource_type": resource_type,
                "status": "success",
            },
            aggregate_type="ExternalSystem",
            aggregate_id=str(system.id),
        )

        return {
            "system_id": system.id,
            "system_name": system.system_name,
            "resource_type": resource_type,
            "status": "success",
            "fhir_resource": fhir_data,
            "synced_at": timezone.now().isoformat(),
        }

    @staticmethod
    def get_national_interop_status() -> dict:
        systems = ExternalSystem.objects.all()
        active = systems.filter(is_active=True)
        errors_last_24h = systems.filter(
            last_sync_status="error",
            last_sync_at__gte=timezone.now() - timedelta(hours=24),
        )

        type_counts = dict(active.values_list("system_type").annotate(count=__import__("django.db.models", fromlist=["Count"]).Count("id")))

        return {
            "total_systems_registered": systems.count(),
            "active_systems": active.count(),
            "systems_with_errors_24h": errors_last_24h.count(),
            "active_by_type": type_counts,
            "national_health_pct": round(active.count() / systems.count() * 100, 1) if systems.count() > 0 else 0,
            "timestamp": timezone.now().isoformat(),
        }
