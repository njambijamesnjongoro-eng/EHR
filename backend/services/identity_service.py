import hashlib
import uuid
from datetime import date
from difflib import SequenceMatcher

from django.db import transaction
from django.db.models import Q

from core.models import Patient, PatientIdentity, PatientMergeLog, EnterpriseAuditEvent


class IdentityService:
    """National patient identity management with duplicate detection."""

    @staticmethod
    def generate_national_health_id(patient: Patient) -> str:
        raw = f"{patient.first_name[:3].upper()}{patient.date_of_birth.strftime('%y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        return f"NHID-{raw[:4]}-{raw[4:8]}-{raw[8:12]}"

    @staticmethod
    def find_duplicates(patient: Patient) -> list:
        candidates = Patient.objects.filter(
            Q(national_id=patient.national_id) |
            Q(phone_number=patient.phone_number) |
            (
                Q(first_name__iexact=patient.first_name) &
                Q(last_name__iexact=patient.last_name) &
                Q(date_of_birth=patient.date_of_birth)
            )
        ).exclude(id=patient.id)

        results = []
        for cand in candidates:
            score = IdentityService._similarity_score(patient, cand)
            if score >= 0.7:
                results.append({"patient": cand, "score": round(score, 2)})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    @staticmethod
    def _similarity_score(a: Patient, b: Patient) -> float:
        scores = []
        if a.national_id and b.national_id and a.national_id == b.national_id:
            scores.append(1.0)
        if a.phone_number and b.phone_number and a.phone_number == b.phone_number:
            scores.append(0.9)
        fn_score = SequenceMatcher(None, a.first_name.lower(), b.first_name.lower()).ratio()
        ln_score = SequenceMatcher(None, a.last_name.lower(), b.last_name.lower()).ratio()
        scores.append((fn_score + ln_score) / 2)
        if a.date_of_birth == b.date_of_birth:
            scores.append(1.0)
        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    @transaction.atomic
    def merge_patients(target: Patient, source: Patient, merged_by, reason: str = ""):
        from core.models import (
            Visit, VitalSign, Diagnosis, Prescription, LabRequest, LabResult,
            Admission, Invoice, ImagingRequest, ImagingResult, Referral,
            TelemedicineSession,
        )

        merge_data = {
            "source_id": source.id,
            "source_health_id": source.health_id,
            "source_name": source.full_name,
            "target_id": target.id,
            "target_health_id": target.health_id,
        }

        related_models = [
            (Visit.objects.filter(patient=source), "patient"),
            (VitalSign.objects.filter(patient=source), "patient"),
            (Diagnosis.objects.filter(patient=source), "patient"),
            (Prescription.objects.filter(patient=source), "patient"),
            (LabRequest.objects.filter(patient=source), "patient"),
            (LabResult.objects.filter(patient=source), "patient"),
            (Admission.objects.filter(patient=source), "patient"),
            (Invoice.objects.filter(patient=source), "patient"),
            (ImagingRequest.objects.filter(patient=source), "patient"),
            (ImagingResult.objects.filter(patient=source), "patient"),
            (Referral.objects.filter(patient=source), "patient"),
            (TelemedicineSession.objects.filter(patient=source), "patient"),
        ]

        for qs, field in related_models:
            count = qs.update(**{field: target})
            merge_data[f"{qs.model.__name__}_records_moved"] = count

        PatientMergeLog.objects.create(
            merged_into=target,
            merged_from=source,
            merged_by=merged_by,
            merge_reason=reason,
            merged_data=merge_data,
        )

        source.is_active = False
        source.save(update_fields=["is_active"])

        EnterpriseAuditEvent.objects.create(
            event_type=EnterpriseAuditEvent.EventType.ADMIN,
            action="patient_merge",
            resource_type="Patient",
            resource_id=str(target.id),
            description=f"Merged patient {source.health_id} into {target.health_id}",
            metadata=merge_data,
        )

        return merge_data
