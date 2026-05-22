from datetime import timedelta

from django.db.models import Count, Avg
from django.utils import timezone

from core.models import (
    SmartHospitalDevice, SmartDeviceEvent,
    Ward, Bed, Admission, PredictiveAlert,
)
from events.event_bus import EventBus


class SmartHospitalAutomationService:
    """Intelligent hospital operations — automated patient flow, resource allocation, bottleneck detection."""

    @staticmethod
    def create_device_event(device_id, hospital_id, event_category, event_type, *,
                            value=None, unit="", payload=None, severity="info") -> SmartDeviceEvent:
        from core.models import SmartHospitalDevice
        device = SmartHospitalDevice.objects.get(id=device_id)

        event = SmartDeviceEvent.objects.create(
            device_id=device_id,
            hospital_id=hospital_id,
            ward_id=device.ward_id,
            event_category=event_category,
            event_type=event_type,
            value=value,
            unit=unit,
            payload=payload or {},
            severity=severity,
            occurred_at=timezone.now(),
        )

        EventBus.emit(
            event_source="system",
            event_type=f"smart_hospital.{event_category}.{event_type}",
            data={
                "event_id": event.id,
                "device_id": device_id,
                "hospital_id": hospital_id,
                "event_type": event_type,
                "severity": severity,
                "value": value,
            },
            aggregate_type="SmartDeviceEvent",
            aggregate_id=str(event.id),
        )

        return event

    @staticmethod
    def analyze_patient_flow(hospital_id: int, days: int = 7) -> dict:
        since = timezone.now() - timedelta(days=days)

        daily_admissions = Admission.objects.filter(
            hospital_id=hospital_id,
            admission_date__gte=since,
        ).extra({"date": "date(admission_date)"}).values("date").annotate(
            count=Count("id"),
        ).order_by("date")

        daily_discharges = Admission.objects.filter(
            hospital_id=hospital_id,
            discharge_date__gte=since,
        ).extra({"date": "date(discharge_date)"}).values("date").annotate(
            count=Count("id"),
        ).order_by("date")

        peak_hour = SmartDeviceEvent.objects.filter(
            hospital_id=hospital_id,
            occurred_at__gte=since,
        ).extra({"hour": "extract(hour from occurred_at)"}).values("hour").annotate(
            count=Count("id"),
        ).order_by("-count").first()

        return {
            "hospital_id": hospital_id,
            "period_days": days,
            "avg_daily_admissions": round(sum(d["count"] for d in daily_admissions) / max(len(daily_admissions), 1), 1),
            "avg_daily_discharges": round(sum(d["count"] for d in daily_discharges) / max(len(daily_discharges), 1), 1),
            "peak_activity_hour": int(peak_hour["hour"]) if peak_hour else None,
            "admission_trend": "increasing" if len(daily_admissions) > 1 and daily_admissions[-1]["count"] > daily_admissions[0]["count"] else "stable",
        }

    @staticmethod
    def detect_bottlenecks(hospital_id: int) -> list:
        bottlenecks = []

        wards = Ward.objects.filter(hospital_id=hospital_id, is_active=True)
        for ward in wards:
            beds = Bed.objects.filter(ward=ward)
            total = beds.count()
            occupied = beds.filter(occupancy_status="occupied").count()
            if total > 0 and occupied / total > 0.9:
                bottlenecks.append({
                    "ward_id": ward.id,
                    "ward_name": ward.ward_name,
                    "type": "capacity",
                    "severity": "critical" if occupied / total > 0.95 else "high",
                    "utilization_pct": round(occupied / total * 100, 1),
                    "recommendation": f"Consider transferring patients from {ward.ward_name} or opening overflow capacity",
                })

        return bottlenecks

    @staticmethod
    def predictive_staffing(hospital_id: int, days_ahead: int = 7) -> dict:
        since = timezone.now() - timedelta(days=30)

        admissions = Admission.objects.filter(
            hospital_id=hospital_id,
            admission_date__gte=since,
        ).count()

        avg_daily = admissions / 30
        current_occupied = Admission.objects.filter(
            hospital_id=hospital_id,
            status=Admission.AdmissionStatus.ACTIVE,
        ).count()

        total_beds = Bed.objects.filter(
            ward__hospital_id=hospital_id,
            occupancy_status__in=["available", "occupied"],
        ).count()

        return {
            "hospital_id": hospital_id,
            "forecast_days": days_ahead,
            "avg_daily_admissions": round(avg_daily, 1),
            "current_occupancy": current_occupied,
            "total_beds": total_beds,
            "projected_occupancy": round(current_occupied + (avg_daily * days_ahead * 0.6), 0),
            "recommended_staff_ratio": "1:4" if total_beds > 100 else "1:3",
            "peak_hours": "08:00-11:00, 14:00-17:00",
        }

    @staticmethod
    def equipment_utilization(hospital_id: int) -> dict:
        devices = SmartHospitalDevice.objects.filter(
            hospital_id=hospital_id, is_active=True,
        )

        return {
            "hospital_id": hospital_id,
            "total_devices": devices.count(),
            "online_devices": devices.filter(is_online=True).count(),
            "offline_devices": devices.filter(is_online=False).count(),
            "by_category": dict(
                devices.values_list("device_category").annotate(count=Count("id")).order_by("device_category")
            ),
        }
