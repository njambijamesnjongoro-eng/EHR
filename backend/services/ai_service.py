import json
import hashlib
import hmac
import time
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from core.models import AIServiceRegistry, AnalyticsEvent, EnterpriseAuditEvent


class AIIntegrationService:
    """AI service integration framework for future ML/AI capabilities."""

    @staticmethod
    def register_service(name, service_type, version="1.0.0", endpoint="", config=None) -> AIServiceRegistry:
        service, created = AIServiceRegistry.objects.get_or_create(
            service_name=name,
            defaults={
                "service_version": version,
                "service_type": service_type,
                "endpoint_url": endpoint,
                "config": config or {},
            },
        )
        if not created:
            service.service_version = version
            service.endpoint_url = endpoint
            service.config = config or {}
            service.save()
        return service

    @staticmethod
    def call_service(service_name: str, payload: dict) -> dict:
        try:
            service = AIServiceRegistry.objects.get(
                service_name=service_name,
                status=AIServiceRegistry.ServiceStatus.ACTIVE,
            )
        except AIServiceRegistry.DoesNotExist:
            return {"success": False, "error": "Service not available"}

        # Future: actual HTTP call to AI service
        # For now, return mock response structure
        return {
            "success": True,
            "service": service.service_name,
            "version": service.service_version,
            "prediction": None,
            "confidence": 0.0,
            "processing_time_ms": 0,
        }

    @staticmethod
    def record_analytics_event(event_type, hospital=None, patient=None, event_data=None, anonymize=False):
        event = AnalyticsEvent.objects.create(
            event_type=event_type,
            hospital=hospital,
            patient=patient if not anonymize else None,
            anonymized=anonymize,
            event_data=event_data or {},
            county=hospital.county if hospital else "",
            occurred_at=timezone.now(),
        )
        return event

    @staticmethod
    def get_feature_vector(patient_id: int) -> dict:
        """Generate a feature vector for ML predictions (future use)."""
        from core.models import Patient, Visit, Diagnosis, LabResult, VitalSign

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {}

        recent_visits = Visit.objects.filter(patient=patient).order_by("-visit_date")[:10]

        diagnoses = Diagnosis.objects.filter(patient=patient).values_list("diagnosis_name", flat=True)
        latest_vitals = VitalSign.objects.filter(patient=patient).order_by("-created_at").first()
        latest_labs = LabResult.objects.filter(patient=patient).order_by("-result_at").first()

        return {
            "patient_id": patient_id,
            "age": patient.age,
            "gender": patient.gender,
            "visit_count_90d": recent_visits.count(),
            "diagnosis_count": diagnoses.count(),
            "diagnosis_list": list(diagnoses[:5]),
            "latest_bmi": float(latest_vitals.bmi) if latest_vitals else None,
            "latest_blood_pressure": {
                "systolic": latest_vitals.blood_pressure_systolic,
                "diastolic": latest_vitals.blood_pressure_diastolic,
            } if latest_vitals else None,
            "latest_lab_abnormal": latest_labs.is_abnormal if latest_labs else None,
        }

    @staticmethod
    def health_check() -> dict:
        services = AIServiceRegistry.objects.filter(
            status__in=[AIServiceRegistry.ServiceStatus.ACTIVE, AIServiceRegistry.ServiceStatus.DEGRADED],
        )
        return {
            "total_services": services.count(),
            "active_services": services.filter(status=AIServiceRegistry.ServiceStatus.ACTIVE).count(),
            "services": [
                {
                    "name": s.service_name,
                    "type": s.service_type,
                    "status": s.status,
                    "version": s.service_version,
                    "last_heartbeat": s.last_heartbeat.isoformat() if s.last_heartbeat else None,
                }
                for s in services
            ],
        }
