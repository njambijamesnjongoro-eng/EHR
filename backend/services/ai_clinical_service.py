import time
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import AIInsight, Patient, Visit, Diagnosis, Prescription, LabResult, VitalSign
from events.event_bus import EventBus


class AIClinicalService:
    """AI-assisted clinical decision support framework.

    All AI outputs are advisory-only and must be reviewed by a clinician.
    """

    @staticmethod
    def create_insight(
        insight_type,
        patient,
        title,
        summary,
        *,
        visit=None,
        details=None,
        confidence_score=0.0,
        source_service="",
    ) -> AIInsight:
        confidence = AIInsight.Confidence.LOW
        if confidence_score >= 0.7:
            confidence = AIInsight.Confidence.HIGH
        elif confidence_score >= 0.4:
            confidence = AIInsight.Confidence.MEDIUM

        insight = AIInsight.objects.create(
            insight_type=insight_type,
            patient=patient,
            visit=visit,
            title=title,
            summary=summary,
            details=details or {},
            confidence=confidence,
            confidence_score=confidence_score,
            source_service=source_service,
        )

        EventBus.emit_ai(
            event_type=f"insight.{insight_type}",
            data={
                "insight_id": insight.id,
                "patient_id": patient.id if patient else None,
                "insight_type": insight_type,
                "confidence_score": confidence_score,
                "title": title,
            },
            aggregate_type="AIInsight",
            aggregate_id=str(insight.id),
        )

        return insight

    @staticmethod
    def assess_risk(patient_id: int) -> AIInsight:
        patient = Patient.objects.get(id=patient_id)
        risk_score = 0.0
        factors = []

        recent_visits = Visit.objects.filter(patient=patient, visit_date__gte=timezone.now() - timedelta(days=90))
        if recent_visits.count() > 5:
            risk_score += 0.2
            factors.append("High visit frequency (>5 in 90 days)")

        active_diagnoses = Diagnosis.objects.filter(patient=patient, is_confirmed=True)
        critical_count = active_diagnoses.filter(severity__in=["severe", "critical"]).count()
        if critical_count > 0:
            risk_score += 0.3
            factors.append(f"{critical_count} critical diagnosis(es)")

        latest_vitals = VitalSign.objects.filter(patient=patient).order_by("-created_at").first()
        if latest_vitals:
            if latest_vitals.blood_pressure_systolic and latest_vitals.blood_pressure_systolic > 160:
                risk_score += 0.2
                factors.append("Elevated blood pressure")
            if latest_vitals.oxygen_saturation and float(latest_vitals.oxygen_saturation) < 90:
                risk_score += 0.3
                factors.append("Low oxygen saturation")

        recent_labs = LabResult.objects.filter(patient=patient, result_at__gte=timezone.now() - timedelta(days=30))
        abnormal_count = recent_labs.filter(is_abnormal=True).count()
        if abnormal_count > 2:
            risk_score += 0.2
            factors.append(f"{abnormal_count} abnormal lab results in 30 days")

        risk_score = min(risk_score, 1.0)

        title = "Patient Risk Assessment"
        summary = f"Risk score: {risk_score:.2f}. Factors: {'; '.join(factors)}" if factors else "No significant risk factors identified."

        return AIClinicalService.create_insight(
            insight_type=AIInsight.InsightType.RISK_ASSESSMENT,
            patient=patient,
            title=title,
            summary=summary,
            details={"risk_score": risk_score, "factors": factors},
            confidence_score=risk_score,
            source_service="clinical_risk_engine",
        )

    @staticmethod
    def check_medication_interactions(patient_id: int) -> AIInsight:
        patient = Patient.objects.get(id=patient_id)
        active_prescriptions = Prescription.objects.filter(patient=patient, is_active=True)
        medications = list(active_prescriptions.values_list("medication_name", flat=True))

        interactions = []
        known_interactions = {
            ("Warfarin", "Aspirin"): "Increased bleeding risk",
            ("ACE Inhibitors", "NSAIDs"): "Reduced antihypertensive effect",
            ("Metformin", "Contrast Dye"): "Risk of lactic acidosis",
            ("Statins", "Macrolide Antibiotics"): "Increased statin toxicity risk",
        }

        for i, med_a in enumerate(medications):
            for med_b in medications[i + 1:]:
                key = (med_a, med_b)
                if key in known_interactions:
                    interactions.append({"medication_a": med_a, "medication_b": med_b, "risk": known_interactions[key]})
                rev_key = (med_b, med_a)
                if rev_key in known_interactions:
                    interactions.append({"medication_a": med_a, "medication_b": med_b, "risk": known_interactions[rev_key]})

        title = "Medication Interaction Check"
        summary = f"Checked {len(medications)} active medication(s). Found {len(interactions)} potential interaction(s)."
        confidence = 0.9 if len(medications) > 0 else 0.0

        return AIClinicalService.create_insight(
            insight_type=AIInsight.InsightType.MEDICATION_CHECK,
            patient=patient,
            title=title,
            summary=summary,
            details={"medications": medications, "interactions": interactions},
            confidence_score=confidence,
            source_service="medication_safety_engine",
        )

    @staticmethod
    def detect_deterioration(patient_id: int) -> AIInsight:
        patient = Patient.objects.get(id=patient_id)
        alerts = []
        score = 0.0

        latest_vitals = VitalSign.objects.filter(patient=patient).order_by("-created_at")[:3]
        previous_vitals = VitalSign.objects.filter(patient=patient).order_by("-created_at")[3:6]

        if len(latest_vitals) >= 2 and len(previous_vitals) >= 2:
            curr_bp = float(latest_vitals[0].blood_pressure_systolic or 0)
            prev_bp = float(previous_vitals[0].blood_pressure_systolic or 0)
            if curr_bp < prev_bp - 20:
                alerts.append(f"Systolic BP dropped {prev_bp - curr_bp} mmHg")
                score += 0.25

            try:
                curr_o2 = float(latest_vitals[0].oxygen_saturation or 100)
                prev_o2 = float(previous_vitals[0].oxygen_saturation or 100)
                if curr_o2 < prev_o2 - 5:
                    alerts.append(f"O2 saturation dropped {prev_o2 - curr_o2}%")
                    score += 0.3
            except (ValueError, TypeError):
                pass

        recent_labs = LabResult.objects.filter(patient=patient).order_by("-result_at")[:5]
        for lab in recent_labs:
            if lab.is_abnormal:
                alerts.append(f"Abnormal lab: {lab.test_name}")
                score += 0.15

        score = min(score, 1.0)
        title = "Deterioration Risk Assessment"
        summary = "; ".join(alerts) if alerts else "No deterioration signals detected."

        return AIClinicalService.create_insight(
            insight_type=AIInsight.InsightType.DETERIORATION_ALERT,
            patient=patient,
            title=title,
            summary=summary,
            details={"deterioration_signals": alerts, "aggregate_score": score},
            confidence_score=score,
            source_service="deterioration_detection_engine",
        )

    @staticmethod
    def review_insight(insight_id: int, reviewer, action_taken: str = ""):
        try:
            insight = AIInsight.objects.get(id=insight_id)
        except AIInsight.DoesNotExist:
            return None

        insight.is_reviewed = True
        insight.reviewed_by = reviewer
        insight.reviewed_at = timezone.now()
        insight.clinical_action_taken = action_taken
        insight.save(update_fields=["is_reviewed", "reviewed_by", "reviewed_at", "clinical_action_taken"])

        EventBus.emit_ai(
            event_type="insight.reviewed",
            data={
                "insight_id": insight.id,
                "reviewed_by": reviewer.id,
                "action_taken": action_taken,
            },
            aggregate_type="AIInsight",
            aggregate_id=str(insight.id),
        )

        return insight
