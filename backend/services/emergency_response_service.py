from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import EmergencyResponseEvent, Hospital, User
from events.event_bus import EventBus


class EmergencyResponseService:
    """National emergency response coordination — incident management, resource dispatch, and regional capacity intelligence."""

    @staticmethod
    def create_emergency_event(emergency_type, severity, title, description, location_region="", affected_counties=None, affected_population=0) -> EmergencyResponseEvent:
        event = EmergencyResponseEvent.objects.create(
            emergency_type=emergency_type,
            severity=severity,
            title=title,
            description=description,
            location_region=location_region,
            affected_counties=affected_counties or [],
            affected_population=affected_population,
        )

        EventBus.emit(
            event_source="system",
            event_type=f"emergency.created.{emergency_type}.{severity}",
            data={
                "event_id": event.id,
                "emergency_type": emergency_type,
                "severity": severity,
                "title": title,
                "region": location_region,
                "affected_population": affected_population,
            },
            aggregate_type="EmergencyResponseEvent",
            aggregate_id=str(event.id),
        )

        return event

    @staticmethod
    def update_incident_status(event_id, status, user) -> EmergencyResponseEvent:
        try:
            event = EmergencyResponseEvent.objects.get(id=event_id)
        except EmergencyResponseEvent.DoesNotExist:
            raise ValueError(f"Emergency event {event_id} not found")

        event.status = status
        if status == EmergencyResponseEvent.Status.RESPONDING:
            event.incident_commander = user
            event.escalated_at = timezone.now()
        elif status == EmergencyResponseEvent.Status.CONTAINED:
            event.contained_at = timezone.now()
        elif status == EmergencyResponseEvent.Status.RESOLVED:
            event.resolved_at = timezone.now()
        event.save()

        EventBus.emit(
            event_source="system",
            event_type=f"emergency.status.{status}",
            data={
                "event_id": event.id,
                "status": status,
                "updated_by": user.id,
            },
            aggregate_type="EmergencyResponseEvent",
            aggregate_id=str(event.id),
        )

        return event

    @staticmethod
    def get_active_emergencies(region=None) -> list:
        qs = EmergencyResponseEvent.objects.filter(
            status__in=["active", "responding", "contained"],
        ).select_related("incident_commander")
        if region:
            qs = qs.filter(location_region=region)
        return list(qs.order_by("-severity", "-created_at"))

    @staticmethod
    def get_regional_capacity_intelligence(region) -> dict:
        from core.models import Ward, Bed

        hospitals = Hospital.objects.filter(region=region, is_active=True)
        hospital_capacity = []

        total_beds = 0
        total_occupied = 0

        for hospital in hospitals:
            wards = Ward.objects.filter(hospital=hospital, is_active=True)
            beds_total = 0
            beds_occupied = 0
            for ward in wards:
                beds = Bed.objects.filter(ward=ward)
                beds_total += beds.count()
                beds_occupied += beds.filter(occupancy_status=Bed.Status.OCCUPIED).count()

            total_beds += beds_total
            total_occupied += beds_occupied

            hospital_capacity.append({
                "hospital_id": hospital.id,
                "hospital_name": hospital.name,
                "total_beds": beds_total,
                "available_beds": beds_total - beds_occupied,
                "utilization_pct": round(beds_occupied / beds_total * 100, 1) if beds_total > 0 else 0,
            })

        return {
            "region": region,
            "hospital_count": hospitals.count(),
            "total_capacity": total_beds,
            "total_available": total_beds - total_occupied,
            "overall_utilization_pct": round(total_occupied / total_beds * 100, 1) if total_beds > 0 else 0,
            "hospitals": hospital_capacity,
            "surge_capacity_pct": round((total_beds - total_occupied) / total_beds * 100, 1) if total_beds > 0 else 0,
        }

    @staticmethod
    def coordinate_response(event_id, resource_needs=None, responding_units=None) -> dict:
        try:
            event = EmergencyResponseEvent.objects.get(id=event_id)
        except EmergencyResponseEvent.DoesNotExist:
            return {"error": "Emergency event not found"}

        if resource_needs:
            existing = event.resource_needs or {}
            existing.update(resource_needs)
            event.resource_needs = existing

        if responding_units:
            existing_units = event.responding_units or []
            existing_units.extend(responding_units)
            event.responding_units = existing_units

        if event.status == EmergencyResponseEvent.Status.ACTIVE:
            event.status = EmergencyResponseEvent.Status.RESPONDING
            event.escalated_at = timezone.now()

        event.save()

        EventBus.emit(
            event_source="system",
            event_type="emergency.response_coordinated",
            data={
                "event_id": event.id,
                "resource_needs": resource_needs,
                "responding_units_count": len(event.responding_units),
            },
            aggregate_type="EmergencyResponseEvent",
            aggregate_id=str(event.id),
        )

        return {
            "event_id": event.id,
            "status": event.status,
            "resource_needs": event.resource_needs,
            "responding_units": event.responding_units,
            "coordination_center": event.coordination_center,
        }

    @staticmethod
    def get_national_emergency_overview() -> dict:
        active = EmergencyResponseEvent.objects.filter(
            status__in=["active", "responding"],
        )
        contained = EmergencyResponseEvent.objects.filter(
            status__in=["contained", "aftermath"],
        )
        resolved = EmergencyResponseEvent.objects.filter(status="resolved")

        severity_breakdown = {}
        for s, _ in EmergencyResponseEvent.Severity.choices:
            count = active.filter(severity=s).count()
            if count > 0:
                severity_breakdown[s] = count

        type_breakdown = {}
        for t, _ in EmergencyResponseEvent.EmergencyType.choices:
            count = active.filter(emergency_type=t).count()
            if count > 0:
                type_breakdown[t] = count

        return {
            "active_emergencies": active.count(),
            "contained_emergencies": contained.count(),
            "resolved_emergencies": resolved.count(),
            "total_affected_population": sum(active.values_list("affected_population", flat=True)),
            "severity_breakdown": severity_breakdown,
            "type_breakdown": type_breakdown,
            "timestamp": timezone.now().isoformat(),
        }
