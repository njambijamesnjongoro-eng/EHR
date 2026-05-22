from datetime import date, timedelta
from collections import defaultdict

from django.db.models import Avg, Count, Sum, FloatField
from django.db.models.functions import TruncMonth
from django.utils import timezone

from core.models import PopulationHealthInsight, Patient, Diagnosis
from events.event_bus import EventBus


class PopulationHealthService:
    """Population health analytics — disease burden, healthcare access, health equity, and regional comparisons."""

    @staticmethod
    def record_population_insight(category, county, indicator_name, indicator_value, population_base, period_start, period_end, **kwargs) -> PopulationHealthInsight:
        insight = PopulationHealthInsight.objects.create(
            category=category,
            county=county,
            sub_county=kwargs.get("sub_county", ""),
            region=kwargs.get("region", ""),
            indicator_name=indicator_name,
            indicator_value=indicator_value,
            population_base=population_base,
            confidence_interval_low=kwargs.get("ci_low"),
            confidence_interval_high=kwargs.get("ci_high"),
            percentile_rank=kwargs.get("percentile_rank"),
            trend_direction=kwargs.get("trend_direction", ""),
            comparison_national=kwargs.get("comparison_national"),
            comparison_regional=kwargs.get("comparison_regional"),
            period_start=period_start,
            period_end=period_end,
            metadata=kwargs.get("metadata", {}),
            is_anonymized=kwargs.get("is_anonymized", True),
        )

        EventBus.emit(
            event_source="system",
            event_type=f"population_health.insight.{category}",
            data={
                "insight_id": insight.id,
                "category": category,
                "county": county,
                "indicator": indicator_name,
                "value": indicator_value,
                "population_base": population_base,
            },
            aggregate_type="PopulationHealthInsight",
            aggregate_id=str(insight.id),
        )

        return insight

    @staticmethod
    def get_disease_burden(county=None, days=365) -> dict:
        since = timezone.now() - timedelta(days=days)

        insights = PopulationHealthInsight.objects.filter(
            category=PopulationHealthInsight.InsightCategory.DISEASE_BURDEN,
            period_end__gte=since,
        )
        if county:
            insights = insights.filter(county=county)

        diagnosis_qs = Diagnosis.objects.filter(
            diagnosed_at__gte=since, is_confirmed=True,
        )
        if county:
            diagnosis_qs = diagnosis_qs.filter(patient__county=county)

        top_conditions = diagnosis_qs.values("icd_code", "diagnosis_name").annotate(
            count=Count("id"),
        ).order_by("-count")[:10]

        return {
            "period_days": days,
            "county": county or "national",
            "total_confirmed_cases": diagnosis_qs.count(),
            "unique_conditions": diagnosis_qs.values("icd_code").distinct().count(),
            "top_conditions": [
                {"icd_code": c["icd_code"], "diagnosis": c["diagnosis_name"], "case_count": c["count"]}
                for c in top_conditions
            ],
            "insights_count": insights.count(),
        }

    @staticmethod
    def get_healthcare_access_metrics(region=None) -> dict:
        qs = PopulationHealthInsight.objects.filter(
            category=PopulationHealthInsight.InsightCategory.HEALTHCARE_ACCESS,
        )
        if region:
            qs = qs.filter(region=region)

        aggregated = qs.aggregate(
            avg_access_score=Avg("indicator_value"),
            total_population=Sum("population_base"),
            insight_count=Count("id"),
        )

        county_breakdown = qs.values("county").annotate(
            avg_score=Avg("indicator_value"),
            population=Sum("population_base"),
        ).order_by("avg_score")

        return {
            "region": region or "national",
            "average_access_score": round(aggregated.get("avg_access_score") or 0, 2),
            "total_population_assessed": aggregated.get("total_population") or 0,
            "counties_assessed": aggregated.get("insight_count") or 0,
            "county_breakdown": list(county_breakdown),
            "access_gap_alert": "High disparity detected" if county_breakdown and
                (county_breakdown.last()["avg_score"] - county_breakdown.first()["avg_score"]) > 30 else "Moderate",
        }

    @staticmethod
    def get_health_equity_analysis() -> dict:
        equity_insights = PopulationHealthInsight.objects.filter(
            category=PopulationHealthInsight.InsightCategory.HEALTH_EQUITY,
        )

        by_county = equity_insights.values("county").annotate(
            avg_value=Avg("indicator_value"),
        ).order_by("avg_value")

        national_avg = equity_insights.aggregate(
            avg=Avg("indicator_value"),
            max=Avg("indicator_value"),
            min=Avg("indicator_value"),
        )

        values = [c["avg_value"] for c in by_county if c["avg_value"]]
        gini_coefficient = 0
        if values and len(values) > 1:
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            cumulative = sum((i + 1) * v for i, v in enumerate(sorted_vals))
            gini_coefficient = (2 * cumulative) / (n * sum(sorted_vals)) - (n + 1) / n

        return {
            "national_avg_score": round(national_avg.get("avg") or 0, 2),
            "counties_analyzed": by_county.count(),
            "gini_coefficient": round(gini_coefficient, 4),
            "highest_equity": list(by_county[:5]),
            "lowest_equity": list(by_county.order_by("-avg_value")[:5]),
            "interpretation": "Higher Gini indicates greater inequity across counties",
            "recommendation": "Focus resources on lowest-equity counties to close the gap",
        }

    @staticmethod
    def get_population_health_trends(indicator, county, months=12) -> dict:
        since = timezone.now() - timedelta(days=months * 30)

        insights = PopulationHealthInsight.objects.filter(
            indicator_name=indicator,
            county=county,
            period_end__gte=since,
        ).order_by("period_end")

        monthly = insights.values("period_end").annotate(
            avg_value=Avg("indicator_value"),
        ).order_by("period_end")

        values = [m["avg_value"] for m in monthly if m["avg_value"]]
        trend = "stable"
        if len(values) >= 2:
            if values[-1] > values[0] * 1.1:
                trend = "increasing"
            elif values[-1] < values[0] * 0.9:
                trend = "decreasing"

        return {
            "indicator": indicator,
            "county": county,
            "months_analyzed": months,
            "data_points": len(monthly),
            "trend": trend,
            "monthly_values": [
                {"period": m["period_end"].isoformat() if hasattr(m["period_end"], "isoformat") else str(m["period_end"]), "value": m["avg_value"]}
                for m in monthly
            ],
        }

    @staticmethod
    def compare_regional_health(regions: list) -> dict:
        comparison = []
        for region in regions:
            insights = PopulationHealthInsight.objects.filter(region=region)
            aggregated = insights.aggregate(
                avg_indicator=Avg("indicator_value"),
                insight_count=Count("id"),
            )
            comparison.append({
                "region": region,
                "average_indicator_score": round(aggregated.get("avg_indicator") or 0, 2),
                "insights_count": aggregated.get("insight_count") or 0,
            })

        return {
            "regions_compared": regions,
            "comparison": comparison,
            "highest_performing": max(comparison, key=lambda r: r["average_indicator_score"]) if comparison else None,
            "lowest_performing": min(comparison, key=lambda r: r["average_indicator_score"]) if comparison else None,
            "recommendation": "Allocate resources to lower-performing regions for equitable health outcomes",
        }
