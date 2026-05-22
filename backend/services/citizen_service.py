from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import (
    CitizenHealthProfile, Patient, Visit, Diagnosis,
    Prescription, LabResult, LabRequest,
    DeviceReading, WearableDevice,
)
from events.event_bus import EventBus


class CitizenPortalService:
    """National citizen health portal service.

    Patients can ONLY access their own records.
    """

    @staticmethod
    def get_or_create_profile(patient) -> CitizenHealthProfile:
        profile, created = CitizenHealthProfile.objects.get_or_create(
            patient=patient,
            defaults={
                "emergency_contacts": [],
                "notification_preferences": {"email": True, "sms": False},
                "consent_settings": {"data_sharing": False, "research": False},
            },
        )
        if not created:
            profile.last_portal_login = timezone.now()
            profile.save(update_fields=["last_portal_login"])
        return profile

    @staticmethod
    def get_health_summary(patient) -> dict:
        profile = CitizenHealthProfile.objects.get_or_create(patient=patient)[0]

        recent_visits = Visit.objects.filter(patient=patient).order_by("-visit_date")[:10]
        diagnoses = Diagnosis.objects.filter(patient=patient, is_confirmed=True)
        active_prescriptions = Prescription.objects.filter(patient=patient, is_active=True)

        lab_requests = LabRequest.objects.filter(patient=patient).order_by("-requested_at")[:10]
        lab_results = LabResult.objects.filter(patient=patient).order_by("-result_at")[:10]

        latest_readings = {}
        for rt in DeviceReading.ReadingType.values:
            reading = DeviceReading.objects.filter(
                patient=patient, reading_type=rt,
            ).order_by("-recorded_at").first()
            if reading:
                latest_readings[rt] = {
                    "value": reading.value,
                    "unit": reading.unit,
                    "recorded_at": reading.recorded_at.isoformat(),
                }

        return {
            "patient": {
                "id": patient.id,
                "health_id": patient.health_id,
                "full_name": patient.full_name,
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "gender": patient.gender,
                "blood_group": patient.blood_group,
                "phone_number": patient.phone_number,
                "email": patient.email,
            },
            "profile": {
                "preferred_language": profile.preferred_language,
                "emergency_contacts": profile.emergency_contacts,
                "allergies_summary": profile.allergies_summary,
                "chronic_conditions_summary": profile.chronic_conditions_summary,
                "medication_summary": profile.medication_summary,
            },
            "recent_visits": [
                {
                    "id": v.id,
                    "date": v.visit_date.isoformat() if hasattr(v.visit_date, "isoformat") else str(v.visit_date),
                    "chief_complaint": v.chief_complaint,
                    "diagnosis_summary": v.diagnosis_summary,
                    "doctor_name": f"{v.doctor.first_name} {v.doctor.last_name}" if v.doctor else "",
                }
                for v in recent_visits
            ],
            "diagnoses": [
                {"name": d.diagnosis_name, "icd_code": d.icd_code, "severity": d.severity, "date": d.diagnosed_at.isoformat()}
                for d in diagnoses[:10]
            ],
            "active_prescriptions": [
                {
                    "medication_name": p.medication_name,
                    "dosage": p.dosage,
                    "frequency": p.frequency,
                    "prescribed_by": f"{p.prescribed_by.first_name} {p.prescribed_by.last_name}" if p.prescribed_by else "",
                }
                for p in active_prescriptions
            ],
            "lab_results": [
                {
                    "test_name": r.test_name,
                    "result_text": r.result_text,
                    "is_abnormal": r.is_abnormal,
                    "date": r.result_at.isoformat() if r.result_at else None,
                }
                for r in lab_results
            ],
            "lab_requests": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "date": r.requested_at.isoformat() if hasattr(r.requested_at, "isoformat") else str(r.requested_at),
                }
                for r in lab_requests
            ],
            "wearable_devices": [
                {"id": d.id, "device_type": d.device_type, "device_name": d.device_name, "is_active": d.is_active, "is_verified": d.is_verified}
                for d in WearableDevice.objects.filter(patient=patient, is_active=True)
            ],
            "latest_readings": latest_readings,
        }

    @staticmethod
    def get_upcoming_appointments(patient) -> list:
        from core.models import TelemedicineSession

        telemed = TelemedicineSession.objects.filter(
            patient=patient,
            status__in=["scheduled"],
            scheduled_at__gte=timezone.now(),
        ).order_by("scheduled_at")[:10]

        return [
            {
                "id": t.id,
                "type": "telemedicine",
                "doctor_name": f"{t.doctor.first_name} {t.doctor.last_name}",
                "scheduled_at": t.scheduled_at.isoformat(),
                "session_type": t.session_type,
                "meeting_url": t.meeting_url,
            }
            for t in telemed
        ]

    @staticmethod
    def update_profile(patient, data: dict) -> CitizenHealthProfile:
        profile = CitizenHealthProfile.objects.get_or_create(patient=patient)[0]

        allowed_fields = [
            "preferred_language", "emergency_contacts", "notification_preferences",
            "allergies_summary", "chronic_conditions_summary",
        ]

        for field in allowed_fields:
            if field in data:
                setattr(profile, field, data[field])

        profile.save()
        return profile

    @staticmethod
    def get_prescription_history(patient) -> list:
        prescriptions = Prescription.objects.filter(patient=patient).select_related(
            "prescribed_by", "dispensed_by",
        ).order_by("-prescribed_at")[:50]

        return [
            {
                "id": p.id,
                "medication_name": p.medication_name,
                "dosage": p.dosage,
                "frequency": p.frequency,
                "route": p.route,
                "duration": p.duration_text,
                "prescribed_by": f"{p.prescribed_by.first_name} {p.prescribed_by.last_name}" if p.prescribed_by else "",
                "prescribed_at": p.prescribed_at.isoformat(),
                "is_active": p.is_active,
                "is_dispensed": p.is_dispensed,
            }
            for p in prescriptions
        ]
