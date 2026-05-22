from datetime import date, timedelta
from collections import defaultdict

from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone

from core.models import PublicHealthMetric, AnalyticsEvent, Diagnosis, Visit, Patient
from events.event_bus import EventBus


class PublicHealthAnalyticsService:
    """Nationwide public health intelligence and epidemiology analytics.

    All results use anonymized, aggregate data only.
    """

    @staticmethod
    def record_metric(
        category, county, metric_value, *,
        unit="", disease_code="", disease_name="",
        population_base=0, sample_size=0,
        period_start=None, period_end=None,
        metadata=None,
    ) -> PublicHealthMetric:
        today = date.today()
        metric = PublicHealthMetric.objects.create(
            metric_category=category,
            county=county,
            disease_code=disease_code,
            disease_name=disease_name,
            metric_value=metric_value,
            metric_unit=unit,
            population_base=population_base,
            sample_size=sample_size,
            period_start=period_start or today - timedelta(days=7),
            period_end=period_end or today,
            metadata=metadata or {},
            is_anonymized=True,
        )

        EventBus.emit(
            event_source="system",
            event_type=f"public_health.{category}",
            data={
                "metric_id": metric.id,
                "county": county,
                "metric_value": metric_value,
                "disease_code": disease_code,
            },
            aggregate_type="PublicHealthMetric",
            aggregate_id=str(metric.id),
        )

        return metric

    @staticmethod
    def disease_prevalence(days: int = 90) -> dict:
        since = timezone.now() - timedelta(days=days)

        diagnoses = Diagnosis.objects.filter(
            diagnosed_at__gte=since, is_confirmed=True,
        ).values("diagnosis_name", "icd_code").annotate(
            count=Count("id"),
        ).order_by("-count")

        return {
            "period_days": days,
            "total_diagnoses": sum(d["count"] for d in diagnoses),
            "diseases": [
                {
                    "diagnosis_name": d["diagnosis_name"],
                    "icd_code": d["icd_code"],
                    "case_count": d["count"],
                }
                for d in diagnoses[:50]
            ],
        }

    @staticmethod
    def outbreak_signals(days: int = 14) -> list:
        since = timezone.now() - timedelta(days=days)
        thirty_days_before = since - timedelta(days=days)

        recent = Diagnosis.objects.filter(
            diagnosed_at__gte=since, is_confirmed=True,
        ).values("icd_code", "diagnosis_name").annotate(
            recent_count=Count("id"),
        )

        baseline = Diagnosis.objects.filter(
            diagnosed_at__gte=thirty_days_before,
            diagnosed_at__lt=since,
            is_confirmed=True,
        ).values("icd_code").annotate(
            baseline_count=Count("id"),
        )

        baseline_map = {b["icd_code"]: b["baseline_count"] for b in baseline}
        signals = []

        for d in recent:
            baseline_count = baseline_map.get(d["icd_code"], 1)
            if baseline_count == 0:
                baseline_count = 1
            ratio = d["recent_count"] / baseline_count
            if ratio > 2.0:
                signals.append({
                    "icd_code": d["icd_code"],
                    "diagnosis_name": d["diagnosis_name"],
                    "recent_count": d["recent_count"],
                    "baseline_count": baseline_count,
                    "ratio": round(ratio, 2),
                    "signal_strength": "high" if ratio > 3.0 else "medium",
                })

        signals.sort(key=lambda x: x["ratio"], reverse=True)
        return signals

    @staticmethod
    def county_disease_heatmap(disease_code: str = None, days: int = 30) -> dict:
        since = timezone.now() - timedelta(days=days)

        visits = Visit.objects.filter(visit_date__gte=since)
        diagnoses = Diagnosis.objects.filter(
            diagnosed_at__gte=since, is_confirmed=True,
        )

        if disease_code:
            diagnoses = diagnoses.filter(icd_code=disease_code)

        county_data = diagnoses.values(
            "visit__patient__county",
        ).annotate(
            case_count=Count("id"),
        ).order_by("-case_count")

        total_patients_by_county = Patient.objects.filter(
            created_at__gte=since,
        ).values("county").annotate(
            total=Count("id", distinct=True),
        )

        patient_map = {p["county"]: p["total"] for p in total_patients_by_county}

        return {
            "disease_code": disease_code or "all",
            "period_days": days,
            "counties": [
                {
                    "county": c["visit__patient__county"] or "Unknown",
                    "case_count": c["case_count"],
                    "population_base": patient_map.get(c["visit__patient__county"], 0),
                }
                for c in county_data
            ],
        }

    @staticmethod
    def healthcare_burden(days: int = 30) -> dict:
        since = timezone.now() - timedelta(days=days)

        total_visits = Visit.objects.filter(visit_date__gte=since).count()
        total_admissions = Diagnosis.objects.filter(diagnosed_at__gte=since).count()
        patients_served = Visit.objects.filter(visit_date__gte=since).values("patient").distinct().count()

        return {
            "period_days": days,
            "total_visits": total_visits,
            "total_diagnoses": total_admissions,
            "patients_served": patients_served,
            "visits_per_day": round(total_visits / days, 1),
            "diagnoses_per_day": round(total_admissions / days, 1),
        }

    @staticmethod
    def vaccination_analytics() -> dict:
        metrics = PublicHealthMetric.objects.filter(
            metric_category=PublicHealthMetric.MetricCategory.VACCINATION_COVERAGE,
        ).order_by("-period_end")[:10]

        return {
            "recent_metrics": [
                {
                    "county": m.county,
                    "coverage": m.metric_value,
                    "population": m.population_base,
                    "period": f"{m.period_start} to {m.period_end}",
                }
                for m in metrics
            ],
        }

    @staticmethod
    def mortality_trends(days: int = 365) -> dict:
        metrics = PublicHealthMetric.objects.filter(
            metric_category=PublicHealthMetric.MetricCategory.MORTALITY,
            period_start__gte=date.today() - timedelta(days=days),
        ).order_by("period_start")

        return {
            "period_days": days,
            "data_points": [
                {
                    "county": m.county,
                    "rate": m.metric_value,
                    "period_start": m.period_start.isoformat(),
                    "period_end": m.period_end.isoformat(),
                }
                for m in metrics
            ],
        }
