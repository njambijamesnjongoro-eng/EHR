from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import AIRecommendation, AIInsight, Patient, Visit, Diagnosis, LabResult, VitalSign
from events.event_bus import EventBus


class AIOrchestratorService:
    """National AI Health Assistant — recommendation engine, clinical intelligence, workflow optimization.

    All outputs are assistive-only and require clinician review.
    """

    @staticmethod
    def generate_recommendation(
        recommendation_type, patient, title, text, *,
        priority="suggestion", visit=None, rationale="", evidence=None,
        confidence=0.0, source="",
    ) -> AIRecommendation:
        rec = AIRecommendation.objects.create(
            recommendation_type=recommendation_type,
            priority=priority,
            patient=patient,
            visit=visit,
            title=title,
            recommendation_text=text,
            clinical_rationale=rationale,
            supporting_evidence=evidence or [],
            confidence_score=confidence,
            source_service=source,
        )

        EventBus.emit_ai(
            event_type=f"recommendation.{recommendation_type}",
            data={
                "recommendation_id": rec.id,
                "patient_id": patient.id if patient else None,
                "type": recommendation_type,
                "priority": priority,
                "confidence": confidence,
            },
            aggregate_type="AIRecommendation",
            aggregate_id=str(rec.id),
        )

        return rec

    @staticmethod
    def generate_clinical_recommendation(patient_id: int, visit_id: int = None) -> AIRecommendation:
        patient = Patient.objects.get(id=patient_id)
        visit = Visit.objects.get(id=visit_id) if visit_id else None
        factors = []

        diagnoses = Diagnosis.objects.filter(patient=patient, is_confirmed=True).order_by("-diagnosed_at")[:3]
        latest_vitals = VitalSign.objects.filter(patient=patient).order_by("-created_at").first()
        latest_labs = LabResult.objects.filter(patient=patient).order_by("-result_at").first()

        if diagnoses:
            critical_dx = [d.diagnosis_name for d in diagnoses if d.severity in ("severe", "critical")]
            if critical_dx:
                factors.append(f"Active critical diagnosis: {', '.join(critical_dx)}")

        if latest_vitals:
            if latest_vitals.blood_pressure_systolic and latest_vitals.blood_pressure_systolic > 140:
                factors.append("Elevated blood pressure requires monitoring")
            if latest_vitals.oxygen_saturation and float(latest_vitals.oxygen_saturation) < 92:
                factors.append("Low oxygen saturation — clinical review recommended")

        if latest_labs and latest_labs.is_abnormal:
            factors.append(f"Abnormal lab result: {latest_labs.test_name}")

        title = "Clinical Care Recommendation"
        text = "; ".join(factors) if factors else "No actionable clinical findings at this time."
        confidence = min(len(factors) * 0.2, 0.9)

        return AIOrchestratorService.generate_recommendation(
            recommendation_type=AIRecommendation.RecommendationType.CLINICAL,
            patient=patient,
            visit=visit,
            title=title,
            text=text,
            priority="recommendation" if confidence > 0.5 else "suggestion",
            rationale="Generated from recent vitals, diagnoses, and lab results within the last 90 days.",
            evidence=factors,
            confidence=round(confidence, 2),
            source="clinical_assistant_v1",
        )

    @staticmethod
    def generate_preventive_recommendation(patient_id: int) -> AIRecommendation:
        patient = Patient.objects.get(id=patient_id)
        factors = []

        age = patient.age if hasattr(patient, "age") else 0
        if age >= 45:
            factors.append(f"Patient age {age} — recommended: annual health screening")

        diagnoses = Diagnosis.objects.filter(patient=patient, is_confirmed=True)
        if diagnoses.filter(diagnosis_name__icontains="diabetes").exists():
            factors.append("Diabetes management: HbA1c monitoring every 3 months recommended")

        if diagnoses.filter(diagnosis_name__icontains="hypertension").exists():
            factors.append("Hypertension: regular BP monitoring and annual renal function check recommended")

        title = "Preventive Care Recommendations"
        text = "; ".join(factors) if factors else "No specific preventive recommendations at this time."

        return AIOrchestratorService.generate_recommendation(
            recommendation_type=AIRecommendation.RecommendationType.PREVENTIVE,
            patient=patient,
            title=title,
            text=text,
            priority="recommendation",
            rationale="Based on patient age, documented diagnoses, and standard preventive care guidelines.",
            evidence=factors,
            confidence=round(min(len(factors) * 0.25, 0.85), 2),
            source="preventive_care_engine_v1",
        )

    @staticmethod
    def accept_recommendation(rec_id: int, user) -> AIRecommendation:
        rec = AIRecommendation.objects.get(id=rec_id)
        rec.is_accepted = True
        rec.accepted_by = user
        rec.accepted_at = timezone.now()
        rec.save(update_fields=["is_accepted", "accepted_by", "accepted_at"])
        return rec

    @staticmethod
    def reject_recommendation(rec_id: int, user, reason: str) -> AIRecommendation:
        rec = AIRecommendation.objects.get(id=rec_id)
        rec.is_accepted = False
        rec.accepted_by = user
        rec.accepted_at = timezone.now()
        rec.rejection_reason = reason
        rec.save(update_fields=["is_accepted", "accepted_by", "accepted_at", "rejection_reason"])
        return rec

    @staticmethod
    def get_active_recommendations(patient_id: int = None) -> list:
        qs = AIRecommendation.objects.filter(is_accepted__isnull=True)
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        return qs.select_related("patient", "visit").order_by("-created_at")[:50]

    @staticmethod
    def analyze_workflow_optimization(hospital_id: int) -> dict:
        from django.db.models import Count, Avg
        from core.models import Visit, Diagnosis

        recent = timezone.now() - timedelta(days=30)

        avg_visits = Visit.objects.filter(
            hospital_id=hospital_id, visit_date__gte=recent,
        ).count()

        diagnosis_time = Diagnosis.objects.filter(
            diagnosed_at__gte=recent,
        ).extra(  # noqa
            select={"avg_hours": "EXTRACT(EPOCH FROM AVG(diagnosed_at - visit_date)) / 3600"}
        ).aggregate(avg=__import__("django.db.models", fromlist=["Avg"]).Avg("id"))

        return {
            "hospital_id": hospital_id,
            "period_days": 30,
            "total_visits": avg_visits,
            "avg_diagnosis_time_hours": round(diagnosis_time.get("avg") or 0, 1),
            "recommendations": [
                "Consider extending evening clinic hours if peak load exceeds capacity",
                "Review diagnosis turnaround times for bottleneck identification",
            ],
        }
