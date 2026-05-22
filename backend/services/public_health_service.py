from datetime import date, timedelta

from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from core.models import AnalyticsEvent, Diagnosis, Visit, Admission, Patient


class PublicHealthService:
    """National public health intelligence with privacy-preserving analytics."""

    @staticmethod
    def disease_surveillance(days: int = 30) -> list:
        since = timezone.now() - timedelta(days=days)
        events = (
            AnalyticsEvent.objects.filter(
                event_type=AnalyticsEvent.EventType.DIAGNOSIS_RECORDED,
                occurred_at__gte=since,
            )
            .values("event_data__diagnosis_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:20]
        )
        return [
            {"diagnosis": e["event_data__diagnosis_name"], "cases": e["count"]}
            for e in events if e["event_data__diagnosis_name"]
        ]

    @staticmethod
    def regional_statistics(county: str = "", days: int = 365):
        since = timezone.now() - timedelta(days=days)
        qs = AnalyticsEvent.objects.filter(occurred_at__gte=since)
        if county:
            qs = qs.filter(county=county)

        return {
            "total_events": qs.count(),
            "by_type": dict(qs.values_list("event_type").annotate(c=Count("id")).order_by("-c")),
            "daily_avg": round(qs.count() / max(days, 1), 1),
        }

    @staticmethod
    def population_health_metrics(days: int = 365):
        since = timezone.now() - timedelta(days=days)

        total_patients = Patient.objects.filter(created_at__gte=since).count()
        total_visits = Visit.objects.filter(visit_date__gte=since).count()
        total_admissions = Admission.objects.filter(admission_date__gte=since).count()

        top_diagnoses = (
            Diagnosis.objects.filter(created_at__gte=since)
            .values("diagnosis_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return {
            "period_days": days,
            "new_patients": total_patients,
            "visits": total_visits,
            "admissions": total_admissions,
            "visits_per_patient": round(total_visits / max(total_patients, 1), 2),
            "admission_rate": round(total_admissions / max(total_visits, 1) * 100, 1),
            "top_diagnoses": list(top_diagnoses),
        }

    @staticmethod
    def anonymized_patient_stats(county: str = ""):
        qs = Patient.objects.filter(is_active=True)
        if county:
            qs = qs.filter(county=county) if hasattr(Patient, 'county') else qs

        age_distribution = {
            "0-17": qs.filter(date_of_birth__gte=date.today() - timedelta(days=365 * 17)).count(),
            "18-35": qs.filter(
                date_of_birth__lte=date.today() - timedelta(days=365 * 18),
                date_of_birth__gte=date.today() - timedelta(days=365 * 35),
            ).count(),
            "36-60": qs.filter(
                date_of_birth__lte=date.today() - timedelta(days=365 * 36),
                date_of_birth__gte=date.today() - timedelta(days=365 * 60),
            ).count(),
            "60+": qs.filter(date_of_birth__lte=date.today() - timedelta(days=365 * 60)).count(),
        }

        return {
            "total_patients": qs.count(),
            "gender_distribution": dict(qs.values_list("gender").annotate(c=Count("id"))),
            "age_distribution": age_distribution,
            "blood_group_distribution": dict(
                qs.values_list("blood_group").annotate(c=Count("id")).order_by("-c")
            ),
        }
