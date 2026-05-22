from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import (
    HealthRiskProfile, Patient, Visit, Diagnosis, VitalSign,
    LabResult, AIInsight,
)
from events.event_bus import EventBus


class PrecisionHealthService:
    """Precision healthcare — risk profiling, longitudinal modeling, personalized care pathways."""

    @staticmethod
    def assess_risk(patient_id: int, risk_category: str) -> HealthRiskProfile:
        patient = Patient.objects.get(id=patient_id)
        score = 0.0
        factors = []
        protective = []

        if risk_category == HealthRiskProfile.RiskCategory.CARDIOVASCULAR:
            vitals = VitalSign.objects.filter(patient=patient).order_by("-created_at")[:5]
            if vitals:
                avg_sys = sum(v.blood_pressure_systolic or 0 for v in vitals) / len(vitals)
                if avg_sys > 140:
                    score += 0.3
                    factors.append(f"Average systolic BP {avg_sys:.0f} (>140)")
                if avg_sys > 160:
                    score += 0.2
                    factors.append("Severe hypertension")

            diagnoses = Diagnosis.objects.filter(patient=patient, is_confirmed=True)
            if diagnoses.filter(diagnosis_name__icontains="diabetes").exists():
                score += 0.2
                factors.append("Diabetes diagnosis")
            if diagnoses.filter(diagnosis_name__icontains="hypertension").exists():
                score += 0.15
                factors.append("Hypertension diagnosis")

            age = patient.age if hasattr(patient, "age") else 0
            if age > 55:
                score += 0.15
                factors.append(f"Age {age} (>55)")
            if age > 65:
                score += 0.1

        elif risk_category == HealthRiskProfile.RiskCategory.DIABETES:
            labs = LabResult.objects.filter(patient=patient).order_by("-result_at")[:5]
            any_glucose = any("glucose" in (r.test_name or "").lower() or "hba1c" in (r.test_name or "").lower() for r in labs)
            if any_glucose:
                score += 0.3
                factors.append("Glucose-related lab results")
            if Diagnosis.objects.filter(patient=patient, is_confirmed=True, diagnosis_name__icontains="obesity").exists():
                score += 0.2
                factors.append("Obesity diagnosis")
            if VitalSign.objects.filter(patient=patient).order_by("-created_at").first():
                v = VitalSign.objects.filter(patient=patient).order_by("-created_at").first()
                if v.bmi and float(v.bmi) > 30:
                    score += 0.2
                    factors.append(f"BMI {float(v.bmi):.1f} (>30)")

        elif risk_category == HealthRiskProfile.RiskCategory.READMISSION:
            recent_visits = Visit.objects.filter(patient=patient, visit_date__gte=timezone.now() - timedelta(days=30))
            visit_count = recent_visits.count()
            if visit_count > 2:
                score += min(visit_count * 0.15, 0.5)
                factors.append(f"{visit_count} visits in 30 days")
            admissions = Admission.objects.filter(patient=patient).count() if hasattr(Admission, 'objects') else 0
            if hasattr(Admission, 'objects'):
                from core.models import Admission
                admissions = Admission.objects.filter(patient=patient).count()
                if admissions > 1:
                    score += 0.2
                    factors.append(f"{admissions} prior admissions")
        else:
            score = 0.1
            factors.append("General risk assessment")

        score = min(score, 1.0)
        level = "critical" if score >= 0.8 else "high" if score >= 0.6 else "moderate" if score >= 0.3 else "low"

        profile, _ = HealthRiskProfile.objects.update_or_create(
            patient=patient,
            risk_category=risk_category,
            defaults={
                "risk_score": round(score, 3),
                "risk_level": level,
                "contributing_factors": factors,
                "protective_factors": protective,
                "last_assessed_at": timezone.now(),
                "is_active": True,
            },
        )

        EventBus.emit_ai(
            event_type=f"risk_profile.{risk_category}",
            data={
                "profile_id": profile.id,
                "patient_id": patient_id,
                "risk_category": risk_category,
                "risk_score": score,
                "risk_level": level,
            },
            aggregate_type="HealthRiskProfile",
            aggregate_id=str(profile.id),
        )

        return profile

    @staticmethod
    def get_patient_risk_summary(patient_id: int) -> dict:
        profiles = HealthRiskProfile.objects.filter(
            patient_id=patient_id, is_active=True,
        )

        return {
            "patient_id": patient_id,
            "overall_risk": "high" if profiles.filter(risk_level__in=["high", "critical"]).exists() else "moderate",
            "profiles": [
                {
                    "category": p.risk_category,
                    "score": p.risk_score,
                    "level": p.risk_level,
                    "assessed_at": p.last_assessed_at.isoformat(),
                    "factors": p.contributing_factors[:5],
                }
                for p in profiles
            ],
        }

    @staticmethod
    def get_high_risk_patients(category: str = None, hospital_id: int = None, limit: int = 50) -> list:
        qs = HealthRiskProfile.objects.filter(
            is_active=True, risk_level__in=["high", "critical"],
        ).select_related("patient")

        if category:
            qs = qs.filter(risk_category=category)
        if hospital_id:
            qs = qs.filter(patient__hospital_id=hospital_id)

        return list(qs.order_by("-risk_score")[:limit])

    @staticmethod
    def get_risk_trends(category: str, days: int = 90) -> dict:
        since = timezone.now() - timedelta(days=days)
        profiles = HealthRiskProfile.objects.filter(
            risk_category=category,
            last_assessed_at__gte=since,
        )

        from django.db.models import Avg
        avg_scores = profiles.values("risk_level").annotate(avg=Avg("risk_score"))

        return {
            "category": category,
            "period_days": days,
            "total_profiles": profiles.count(),
            "by_level": dict(
                profiles.values_list("risk_level").annotate(count=__import__("django.db.models", fromlist=["Count"]).Count("id"))
            ),
            "avg_score_by_level": {a["risk_level"]: round(a["avg"], 3) for a in avg_scores},
        }
