import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import WearableDevice, DeviceReading, PredictiveAlert
from events.event_bus import EventBus


class WearableService:
    """Wearable device management and IoT data ingestion."""

    @staticmethod
    def register_device(patient, device_type, device_name, **kwargs) -> WearableDevice:
        pairing_token = secrets.token_hex(32)

        device = WearableDevice.objects.create(
            patient=patient,
            device_type=device_type,
            device_name=device_name,
            pairing_token=pairing_token,
            **{k: v for k, v in kwargs.items() if hasattr(WearableDevice, k)},
        )

        EventBus.emit_wearable(
            event_type="device.registered",
            data={
                "device_id": device.id,
                "patient_id": patient.id,
                "device_type": device_type,
                "device_name": device_name,
            },
            aggregate_type="WearableDevice",
            aggregate_id=str(device.id),
        )

        return device

    @staticmethod
    def verify_device(device_id: int, pairing_token: str) -> bool:
        try:
            device = WearableDevice.objects.get(id=device_id)
        except WearableDevice.DoesNotExist:
            return False

        if device.pairing_token == pairing_token:
            device.is_verified = True
            device.save(update_fields=["is_verified"])
            return True
        return False

    @staticmethod
    def ingest_reading(device_id: int, patient_id: int, reading_type: str, value: float, unit: str = "", recorded_at=None, metadata=None) -> DeviceReading:
        try:
            device = WearableDevice.objects.get(id=device_id, patient_id=patient_id, is_active=True)
        except WearableDevice.DoesNotExist:
            raise ValueError("Device not found or inactive")

        reading = DeviceReading.objects.create(
            device=device,
            patient_id=patient_id,
            reading_type=reading_type,
            value=value,
            unit=unit,
            recorded_at=recorded_at or timezone.now(),
            metadata=metadata or {},
        )

        WearableService._check_abnormal(reading)
        device.last_sync_at = timezone.now()
        device.save(update_fields=["last_sync_at"])

        EventBus.emit_wearable(
            event_type=f"reading.{reading_type}",
            data={
                "reading_id": reading.id,
                "device_id": device_id,
                "patient_id": patient_id,
                "reading_type": reading_type,
                "value": value,
                "unit": unit,
                "is_abnormal": reading.is_abnormal,
            },
            aggregate_type="DeviceReading",
            aggregate_id=str(reading.id),
        )

        return reading

    @staticmethod
    def bulk_ingest(readings_data: list) -> list:
        results = []
        errors = []

        for data in readings_data:
            try:
                reading = WearableService.ingest_reading(
                    device_id=data["device_id"],
                    patient_id=data["patient_id"],
                    reading_type=data["reading_type"],
                    value=data["value"],
                    unit=data.get("unit", ""),
                    recorded_at=data.get("recorded_at"),
                    metadata=data.get("metadata"),
                )
                results.append(reading)
            except ValueError as e:
                errors.append({"data": data, "error": str(e)})

        return results

    @staticmethod
    def _check_abnormal(reading: DeviceReading):
        abnormal = False
        thresholds = {
            DeviceReading.ReadingType.HEART_RATE: {"min": 40, "max": 200},
            DeviceReading.ReadingType.OXYGEN_SATURATION: {"min": 85, "max": 100},
            DeviceReading.ReadingType.GLUCOSE: {"min": 40, "max": 500},
            DeviceReading.ReadingType.TEMPERATURE: {"min": 34, "max": 42},
        }

        threshold = thresholds.get(reading.reading_type)
        if threshold:
            if reading.value < threshold["min"] or reading.value > threshold["max"]:
                abnormal = True

        if abnormal:
            reading.is_abnormal = True
            reading.save(update_fields=["is_abnormal"])

            PredictiveAlert.objects.create(
                category=PredictiveAlert.AlertCategory.ANOMALY,
                severity=PredictiveAlert.Severity.WARNING,
                title=f"Abnormal {reading.get_reading_type_display()} Reading",
                description=f"{reading.get_reading_type_display()} = {reading.value}{reading.unit} (patient {reading.patient_id})",
                predicted_at=timezone.now(),
                confidence_score=0.8,
                patient=reading.patient,
                metadata={
                    "reading_id": reading.id,
                    "reading_type": reading.reading_type,
                    "value": reading.value,
                    "threshold": threshold,
                },
            )

    @staticmethod
    def get_readings(patient_id: int, reading_type: str = None, hours: int = 24):
        qs = DeviceReading.objects.filter(patient_id=patient_id)
        if reading_type:
            qs = qs.filter(reading_type=reading_type)
        qs = qs.filter(recorded_at__gte=timezone.now() - timedelta(hours=hours))
        return qs.order_by("-recorded_at")

    @staticmethod
    def get_patient_devices(patient_id: int):
        return WearableDevice.objects.filter(patient_id=patient_id, is_active=True)

    @staticmethod
    def get_latest_readings(patient_id: int):
        latest = {}
        for rt in DeviceReading.ReadingType.values:
            reading = DeviceReading.objects.filter(
                patient_id=patient_id, reading_type=rt,
            ).order_by("-recorded_at").first()
            if reading:
                latest[rt] = {"value": reading.value, "unit": reading.unit, "recorded_at": reading.recorded_at.isoformat()}
        return latest
