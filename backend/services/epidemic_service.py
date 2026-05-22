from datetime import date, timedelta
from collections import defaultdict

from django.db.models import Count, Avg, Q
from django.utils import timezone

from core.models import (
    EpidemicAlert, PublicHealthMetric, PublicHealthForecast,
    Diagnosis, Visit, Patient, AnalyticsEvent,
)
from events.event_bus import EventBus


class EpidemicIntelligenceService:
    """Nationwide epidemic intelligence — surveillance, forecasting, and early warning."""

    @staticmethod
    def create_alert(
        alert_level, alert_source, disease_code, disease_name, county, *,
        confirmed=0, suspected=0, deaths=0, attack_rate=0.0,
        r0=None, doubling_time=None, population=0, signal=0.0,
        actions="", metadata=None,
    ) -> EpidemicAlert:
        alert = EpidemicAlert.objects.create(
            alert_level=alert_level,
            alert_source=alert_source,
            disease_code=disease_code,
            disease_name=disease_name,
            county=county,
            confirmed_cases=confirmed,
            suspected_cases=suspected,
            reported_deaths=deaths,
            attack_rate=attack_rate,
            r0_estimate=r0,
            doubling_time_days=doubling_time,
            affected_population=population,
            signal_strength=signal,
            recommended_actions=actions,
            metadata=metadata or {},
            detected_at=timezone.now(),
        )

        EventBus.emit(
            event_source="system",
            event_type=f"epidemic.alert.{alert_level}",
            data={
                "alert_id": alert.id,
                "disease": disease_name,
                "county": county,
                "level": alert_level,
                "signal": signal,
            },
            aggregate_type="EpidemicAlert",
            aggregate_id=str(alert.id),
        )

        return alert

    @staticmethod
    def detect_outbreak_patterns(days: int = 7) -> list:
        since = timezone.now() - timedelta(days=days)
        alerts = []

        disease_counts = Diagnosis.objects.filter(
            diagnosed_at__gte=since, is_confirmed=True,
        ).values("icd_code", "diagnosis_name").annotate(
            count=Count("id"),
        ).order_by("-count")

        for d in disease_counts[:20]:
            if d["count"] >= 3:
                seven_days_before = since - timedelta(days=days)
                baseline = Diagnosis.objects.filter(
                    diagnosed_at__gte=seven_days_before,
                    diagnosed_at__lt=since,
                    icd_code=d["icd_code"],
                    is_confirmed=True,
                ).count()

                if baseline > 0:
                    ratio = d["count"] / baseline
                    if ratio >= 2.0:
                        level = EpidemicAlert.AlertLevel.ORANGE if ratio >= 3.0 else EpidemicAlert.AlertLevel.YELLOW
                        alert = EpidemicIntelligenceService.create_alert(
                            alert_level=level,
                            alert_source=EpidemicAlert.AlertSource.SYNDROMIC,
                            disease_code=d["icd_code"],
                            disease_name=d["diagnosis_name"],
                            county="national",
                            confirmed=d["count"],
                            signal=ratio,
                            actions=f"Investigate {d['diagnosis_name']} cases — ratio {ratio:.1f}x baseline",
                        )
                        alerts.append(alert)

        return alerts

    @staticmethod
    def regional_spread_model(disease_code: str, days: int = 30) -> dict:
        since = timezone.now() - timedelta(days=days)

        county_cases = Diagnosis.objects.filter(
            icd_code=disease_code, diagnosed_at__gte=since, is_confirmed=True,
        ).values("visit__patient__county").annotate(
            case_count=Count("id"),
        ).order_by("-case_count")

        case_list = [{"county": c["visit__patient__county"] or "Unknown", "cases": c["case_count"]} for c in county_cases]

        return {
            "disease_code": disease_code,
            "period_days": days,
            "total_cases": sum(c["cases"] for c in case_list),
            "affected_counties": len(case_list),
            "county_breakdown": case_list,
            "spread_pattern": "multifocal" if len(case_list) > 3 else "localized",
        }

    @staticmethod
    def generate_forecast(disease_code: str, county: str, days_ahead: int = 14) -> PublicHealthForecast:
        since = timezone.now() - timedelta(days=90)

        historical = Diagnosis.objects.filter(
            icd_code=disease_code,
            diagnosed_at__gte=since,
            is_confirmed=True,
        ).count()

        recent = Diagnosis.objects.filter(
            icd_code=disease_code,
            diagnosed_at__gte=timezone.now() - timedelta(days=14),
            is_confirmed=True,
        ).count()

        daily_rate = recent / 14 if recent > 0 else historical / 90
        predicted = daily_rate * days_ahead

        forecast = PublicHealthForecast.objects.create(
            forecast_category=PublicHealthForecast.ForecastCategory.DISEASE,
            county=county,
            disease_code=disease_code,
            disease_name=Diagnosis.objects.filter(icd_code=disease_code).values_list("diagnosis_name", flat=True).first() or "",
            forecast_date=date.today() + timedelta(days=days_ahead),
            predicted_cases=predicted,
            predicted_lower=predicted * 0.7,
            predicted_upper=predicted * 1.3,
            seasonality_factor=1.0,
            trend_direction="increasing" if daily_rate > historical / 90 else "decreasing",
            risk_level="high" if daily_rate > historical / 90 * 1.5 else "moderate" if daily_rate > historical / 90 else "low",
            model_name="trend_extrapolation_v1",
        )

        return forecast

    @staticmethod
    def get_active_alerts(county: str = None) -> list:
        qs = EpidemicAlert.objects.filter(is_active=True)
        if county:
            qs = qs.filter(county=county)
        return qs.order_by("-signal_strength")[:50]

    @staticmethod
    def resolve_alert(alert_id: int) -> EpidemicAlert:
        alert = EpidemicAlert.objects.get(id=alert_id)
        alert.is_active = False
        alert.resolved_at = timezone.now()
        alert.save(update_fields=["is_active", "resolved_at"])
        return alert
