from datetime import timedelta

from django.db.models import Count, Avg
from django.utils import timezone

from core.models import (
    SmartDeviceEvent, SmartHospitalDevice, DeviceReading,
    WearableDevice, Patient, PredictiveAlert,
)
from events.event_bus import EventBus


class AdvancedIoTService:
    """Expanded IoT ecosystem — real-time event ingestion, device health monitoring, distributed processing."""

    @staticmethod
    def ingest_smart_event(device_id, event_category, event_type, *, value=None, payload=None, severity="info") -> SmartDeviceEvent:
        from core.models import SmartHospitalDevice
        try:
            device = SmartHospitalDevice.objects.get(id=device_id)
        except SmartHospitalDevice.DoesNotExist:
            raise ValueError("Device not found")

        event = SmartDeviceEvent.objects.create(
            device=device,
            hospital=device.hospital,
            ward=device.ward,
            event_category=event_category,
            event_type=event_type,
            value=value,
            payload=payload or {},
            severity=severity,
            occurred_at=timezone.now(),
        )

        if severity in ("critical", "emergency"):
            PredictiveAlert.objects.create(
                category=PredictiveAlert.AlertCategory.ANOMALY,
                severity=severity,
                title=f"Device Alert: {device.device_name}",
                description=f"{device.get_device_category_display()} event: {event_type}",
                predicted_at=timezone.now(),
                confidence_score=0.8,
                hospital=device.hospital,
                metadata={"device_id": device.id, "event_id": event.id, "event_type": event_type},
            )

        EventBus.emit(
            event_source="system",
            event_type=f"iot.{event_category}.{event_type}",
            data={
                "event_id": event.id,
                "device_id": device.id,
                "hospital_id": device.hospital_id,
                "category": event_category,
                "event_type": event_type,
                "severity": severity,
            },
            aggregate_type="SmartDeviceEvent",
            aggregate_id=str(event.id),
        )

        return event

    @staticmethod
    def get_device_health(device_id: int) -> dict:
        try:
            device = SmartHospitalDevice.objects.get(id=device_id)
        except SmartHospitalDevice.DoesNotExist:
            return {"error": "Device not found"}

        since = timezone.now() - timedelta(hours=24)
        recent_events = SmartDeviceEvent.objects.filter(device=device, occurred_at__gte=since).count()
        recent_errors = SmartDeviceEvent.objects.filter(
            device=device, occurred_at__gte=since,
            severity__in=["critical", "emergency"],
        ).count()

        return {
            "device_id": device.id,
            "device_name": device.device_name,
            "category": device.device_category,
            "is_online": device.is_online,
            "is_active": device.is_active,
            "last_heartbeat": device.last_heartbeat,
            "firmware_version": device.firmware_version,
            "events_24h": recent_events,
            "errors_24h": recent_errors,
            "health_score": max(0, 100 - recent_errors * 20),
            "status": "healthy" if (device.is_online and recent_errors == 0) else "degraded" if device.is_online else "offline",
        }

    @staticmethod
    def get_hospital_iot_summary(hospital_id: int) -> dict:
        total_devices = SmartHospitalDevice.objects.filter(hospital_id=hospital_id).count()
        online = SmartHospitalDevice.objects.filter(hospital_id=hospital_id, is_online=True).count()
        offline = total_devices - online

        since = timezone.now() - timedelta(hours=1)
        recent_events = SmartDeviceEvent.objects.filter(hospital_id=hospital_id, occurred_at__gte=since).count()
        critical_events = SmartDeviceEvent.objects.filter(
            hospital_id=hospital_id, occurred_at__gte=since,
            severity__in=["critical", "emergency"],
        ).count()

        return {
            "hospital_id": hospital_id,
            "total_devices": total_devices,
            "online": online,
            "offline": offline,
            "events_last_hour": recent_events,
            "critical_events_last_hour": critical_events,
            "uptime_pct": round(online / total_devices * 100, 1) if total_devices > 0 else 0,
        }

    @staticmethod
    def get_patient_wearable_summary(patient_id: int) -> dict:
        devices = WearableDevice.objects.filter(patient_id=patient_id, is_active=True)

        since = timezone.now() - timedelta(hours=24)
        readings = DeviceReading.objects.filter(patient_id=patient_id, recorded_at__gte=since)
        abnormal = readings.filter(is_abnormal=True).count()

        return {
            "patient_id": patient_id,
            "active_devices": devices.count(),
            "readings_24h": readings.count(),
            "abnormal_readings": abnormal,
            "last_reading": readings.order_by("-recorded_at").first().recorded_at.isoformat() if readings.first() else None,
        }

    @staticmethod
    def detect_emergency(patient_id: int) -> bool:
        since = timezone.now() - timedelta(minutes=5)
        recent = DeviceReading.objects.filter(patient_id=patient_id, recorded_at__gte=since)

        for reading in recent:
            if reading.is_abnormal:
                thresholds = {
                    "heart_rate": (120, 40),
                    "oxygen_saturation": (None, 85),
                    "glucose": (400, 50),
                }
                if reading.reading_type in thresholds:
                    high, low = thresholds[reading.reading_type]
                    if (high and reading.value > high) or (low and reading.value < low):
                        return True
        return False
