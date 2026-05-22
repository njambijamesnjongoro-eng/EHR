from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import (
    Patient, CitizenHealthProfile, WearableDevice, DeviceReading,
    TelemedicineSession, TelemedicineInteraction, Prescription,
    LabResult, Diagnosis, Visit, AIInsight, AIRecommendation,
)
from events.event_bus import EventBus


class CitizenSuperPortalService:
    """National citizen health super-portal — lifetime medical history, secure health sharing, preventive care."""

    @staticmethod
    def get_full_health_record(patient) -> dict:
        profile = CitizenHealthProfile.objects.get_or_create(patient=patient)[0]

        visits = Visit.objects.filter(patient=patient).select_related("doctor").order_by("-visit_date")[:20]
        diagnoses = Diagnosis.objects.filter(patient=patient, is_confirmed=True).order_by("-diagnosed_at")[:30]
        prescriptions = Prescription.objects.filter(patient=patient).order_by("-prescribed_at")[:30]
        labs = LabResult.objects.filter(patient=patient).order_by("-result_at")[:20]
        devices = WearableDevice.objects.filter(patient=patient, is_active=True)

        latest_readings = {}
        for reading in DeviceReading.objects.filter(patient=patient).select_related("device").order_by("-recorded_at")[:50]:
            rt = reading.reading_type
            if rt not in latest_readings:
                latest_readings[rt] = {"value": reading.value, "unit": reading.unit, "recorded_at": reading.recorded_at.isoformat()}

        telemed = TelemedicineSession.objects.filter(patient=patient).order_by("-scheduled_at")[:10]
        insights = AIInsight.objects.filter(patient=patient).order_by("-created_at")[:10]
        recommendations = AIRecommendation.objects.filter(patient=patient).order_by("-created_at")[:10]

        return {
            "patient": {
                "health_id": patient.health_id,
                "full_name": patient.full_name,
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "gender": patient.gender,
                "blood_group": patient.blood_group,
                "phone": patient.phone_number,
                "email": patient.email,
            },
            "profile": {
                "preferred_language": profile.preferred_language,
                "allergies": profile.allergies_summary,
                "chronic_conditions": profile.chronic_conditions_summary,
                "medications": profile.medication_summary,
                "emergency_contacts": profile.emergency_contacts,
            },
            "recent_visits": [
                {"id": v.id, "date": v.visit_date.isoformat() if hasattr(v.visit_date, "isoformat") else str(v.visit_date),
                 "complaint": v.chief_complaint, "doctor": f"{v.doctor.first_name} {v.doctor.last_name}" if v.doctor else ""}
                for v in visits
            ],
            "diagnoses": [
                {"name": d.diagnosis_name, "icd": d.icd_code, "severity": d.severity, "date": d.diagnosed_at.isoformat()}
                for d in diagnoses
            ],
            "active_prescriptions": [
                {"medication": p.medication_name, "dosage": p.dosage, "frequency": p.frequency, "prescribed_at": p.prescribed_at.isoformat()}
                for p in prescriptions if p.is_active
            ],
            "lab_results": [
                {"test": r.test_name, "result": r.result_text, "abnormal": r.is_abnormal, "date": r.result_at.isoformat() if r.result_at else None}
                for r in labs
            ],
            "wearable_devices": [
                {"id": d.id, "type": d.device_type, "name": d.device_name, "verified": d.is_verified, "last_sync": d.last_sync_at.isoformat() if d.last_sync_at else None}
                for d in devices
            ],
            "latest_readings": latest_readings,
            "telemedicine": [
                {"id": t.id, "doctor": f"{t.doctor.first_name} {t.doctor.last_name}" if t.doctor else "",
                 "scheduled": t.scheduled_at.isoformat(), "status": t.status, "type": t.session_type}
                for t in telemed
            ],
            "ai_insights": [
                {"id": i.id, "type": i.insight_type, "title": i.title, "confidence": i.confidence, "created": i.created_at.isoformat()}
                for i in insights
            ],
            "ai_recommendations": [
                {"id": r.id, "type": r.recommendation_type, "title": r.title, "priority": r.priority, "created": r.created_at.isoformat()}
                for r in recommendations
            ],
        }

    @staticmethod
    def get_emergency_profile(patient) -> dict:
        profile = CitizenHealthProfile.objects.get_or_create(patient=patient)[0]

        return {
            "patient": {
                "full_name": patient.full_name,
                "health_id": patient.health_id,
                "blood_group": patient.blood_group,
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            },
            "emergency": {
                "contacts": profile.emergency_contacts,
                "allergies": profile.allergies_summary,
                "chronic_conditions": profile.chronic_conditions_summary,
                "medications": profile.medication_summary,
            },
            "active_prescriptions": list(
                Prescription.objects.filter(patient=patient, is_active=True).values(
                    "medication_name", "dosage", "frequency",
                )
            ),
        }

    @staticmethod
    def share_health_data(patient, recipient_email: str, data_types: list, expiry_hours: int = 24):
        import secrets, json
        share_token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=expiry_hours)

        share_data = {"patient_id": patient.id, "data_types": data_types, "token": share_token}

        EventBus.emit(
            event_source="system",
            event_type="citizen.data_shared",
            data=share_data,
            metadata={"recipient": recipient_email, "expires_at": expires_at.isoformat()},
            aggregate_type="CitizenHealthProfile",
            aggregate_id=str(patient.id),
        )

        return {"share_token": share_token, "expires_at": expires_at.isoformat()}

    @staticmethod
    def get_care_reminders(patient) -> list:
        reminders = []

        screenings = {
            "blood_pressure": "Blood pressure check every 6 months",
            "blood_sugar": "Blood sugar screening every 12 months",
            "eye_exam": "Eye examination every 24 months",
            "dental": "Dental check-up every 6 months",
        }

        for key, text in screenings.items():
            reminders.append({"type": key, "message": text, "priority": "routine"})

        active_diagnoses = Diagnosis.objects.filter(patient=patient, is_confirmed=True)
        if active_diagnoses.filter(diagnosis_name__icontains="diabetes").exists():
            reminders.append({"type": "hba1c", "message": "HbA1c test recommended every 3 months", "priority": "important"})

        return reminders
