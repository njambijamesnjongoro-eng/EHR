from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import SmartHospitalDevice, DeviceReading, PredictiveAlert, Ward, Bed
from events.event_bus import EventBus


class SmartHospitalService:
    """Smart hospital device integration and monitoring framework.

    Infrastructure layer — actual hardware integration is future work.
    """

    @staticmethod
    def register_device(hospital, device_category, device_name, serial_number, **kwargs) -> SmartHospitalDevice:
        device = SmartHospitalDevice.objects.create(
            hospital=hospital,
            device_category=device_category,
            device_name=device_name,
            serial_number=serial_number,
            **{k: v for k, v in kwargs.items() if hasattr(SmartHospitalDevice, k)},
        )

        EventBus.emit_integration(
            event_type="smart_hospital.device_registered",
            data={
                "device_id": device.id,
                "hospital_id": hospital.id,
                "category": device_category,
                "name": device_name,
            },
            aggregate_type="SmartHospitalDevice",
            aggregate_id=str(device.id),
        )

        return device

    @staticmethod
    def record_heartbeat(device_id: int) -> bool:
        try:
            device = SmartHospitalDevice.objects.get(id=device_id)
            device.is_online = True
            device.last_heartbeat = timezone.now()
            device.save(update_fields=["is_online", "last_heartbeat"])
            return True
        except SmartHospitalDevice.DoesNotExist:
            return False

    @staticmethod
    def mark_offline(device_id: int):
        try:
            device = SmartHospitalDevice.objects.get(id=device_id)
            device.is_online = False
            device.save(update_fields=["is_online"])
        except SmartHospitalDevice.DoesNotExist:
            pass

    @staticmethod
    def get_hospital_devices(hospital_id: int, category: str = None):
        qs = SmartHospitalDevice.objects.filter(hospital_id=hospital_id, is_active=True)
        if category:
            qs = qs.filter(device_category=category)
        return qs.order_by("device_category", "device_name")

    @staticmethod
    def get_ward_devices(ward_id: int):
        return SmartHospitalDevice.objects.filter(ward_id=ward_id, is_active=True).order_by("device_category")

    @staticmethod
    def detect_offline_devices(hospital_id: int = None, minutes: int = 15) -> list:
        threshold = timezone.now() - timedelta(minutes=minutes)
        qs = SmartHospitalDevice.objects.filter(
            is_active=True,
            last_heartbeat__lt=threshold,
        ) | SmartHospitalDevice.objects.filter(
            is_active=True,
            last_heartbeat__isnull=True,
        )

        if hospital_id:
            qs = qs.filter(hospital_id=hospital_id)

        for device in qs:
            device.is_online = False
            device.save(update_fields=["is_online"])

        return list(qs)

    @staticmethod
    def get_bed_occupancy_summary(hospital_id: int) -> dict:
        wards = Ward.objects.filter(hospital_id=hospital_id, is_active=True)
        summary = []

        for ward in wards:
            beds = Bed.objects.filter(ward=ward)
            total = beds.count()
            occupied = beds.filter(occupancy_status=Bed.Status.OCCUPIED).count()
            summary.append({
                "ward_id": ward.id,
                "ward_name": ward.ward_name,
                "ward_type": ward.ward_type,
                "total_beds": total,
                "occupied": occupied,
                "available": total - occupied,
                "utilization_pct": round(occupied / total * 100, 1) if total > 0 else 0,
            })

        return {
            "hospital_id": hospital_id,
            "wards": summary,
            "total_beds": sum(w["total_beds"] for w in summary),
            "total_occupied": sum(w["occupied"] for w in summary),
            "total_available": sum(w["available"] for w in summary),
            "overall_utilization_pct": round(
                sum(w["occupied"] for w in summary) / sum(w["total_beds"] for w in summary) * 100, 1
            ) if sum(w["total_beds"] for w in summary) > 0 else 0,
        }
