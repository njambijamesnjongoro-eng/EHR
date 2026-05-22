from datetime import timedelta
from collections import defaultdict

from django.db.models import Count, Avg, Q
from django.utils import timezone

from core.models import (
    OperationalAlert, Ward, Bed, Admission, Visit, Patient,
    SmartHospitalMetric,
)
from events.event_bus import EventBus


class OperationalIntelligenceService:
    """Hospital operational intelligence — load analysis, resource prediction, and efficiency optimization."""

    @staticmethod
    def analyze_hospital_load(hospital_id, days=7) -> dict:
        since = timezone.now() - timedelta(days=days)

        wards = Ward.objects.filter(hospital_id=hospital_id, is_active=True)
        ward_metrics = []
        total_beds = 0
        total_occupied = 0

        for ward in wards:
            beds = Bed.objects.filter(ward=ward)
            ward_total = beds.count()
            ward_occupied = beds.filter(occupancy_status=Bed.Status.OCCUPIED).count()
            utilization = round(ward_occupied / ward_total * 100, 1) if ward_total > 0 else 0
            total_beds += ward_total
            total_occupied += ward_occupied

            ward_metrics.append({
                "ward_id": ward.id,
                "ward_name": ward.ward_name,
                "ward_type": ward.ward_type,
                "total_beds": ward_total,
                "occupied": ward_occupied,
                "available": ward_total - ward_occupied,
                "utilization_pct": utilization,
            })

        visit_count = Visit.objects.filter(
            hospital_id=hospital_id, visit_date__gte=since,
        ).count()

        admission_count = Admission.objects.filter(
            hospital_id=hospital_id, admitted_at__gte=since,
        ).count()

        return {
            "hospital_id": hospital_id,
            "period_days": days,
            "total_beds": total_beds,
            "total_occupied": total_occupied,
            "overall_utilization_pct": round(total_occupied / total_beds * 100, 1) if total_beds > 0 else 0,
            "total_visits": visit_count,
            "total_admissions": admission_count,
            "daily_avg_visits": round(visit_count / days, 1),
            "daily_avg_admissions": round(admission_count / days, 1),
            "ward_breakdown": ward_metrics,
        }

    @staticmethod
    def predict_resource_allocation(hospital_id, days_ahead=7) -> dict:
        since = timezone.now() - timedelta(days=30)
        recent = timezone.now() - timedelta(days=7)

        historical_visits = Visit.objects.filter(
            hospital_id=hospital_id, visit_date__gte=since,
        ).count()

        recent_visits = Visit.objects.filter(
            hospital_id=hospital_id, visit_date__gte=recent,
        ).count()

        daily_rate = recent_visits / 7 if recent_visits > 0 else historical_visits / 30
        projected_visits = int(daily_rate * days_ahead)

        ward_needs = []
        wards = Ward.objects.filter(hospital_id=hospital_id, is_active=True)
        for ward in wards:
            beds = Bed.objects.filter(ward=ward)
            ward_total = beds.count()
            ward_occupied = beds.filter(occupancy_status=Bed.Status.OCCUPIED).count()
            util = ward_occupied / ward_total if ward_total > 0 else 0
            needed = max(0, int(ward_total * (util + 0.1)) - ward_occupied)

            ward_needs.append({
                "ward_name": ward.ward_name,
                "current_utilization_pct": round(util * 100, 1),
                "additional_beds_needed": needed,
            })

        return {
            "hospital_id": hospital_id,
            "forecast_days": days_ahead,
            "projected_visits": projected_visits,
            "projected_admissions": int(projected_visits * 0.3),
            "ward_projections": ward_needs,
            "total_additional_beds": sum(w["additional_beds_needed"] for w in ward_needs),
            "staffing_recommendation": "Increase nursing staff by 15% to match projected load",
            "equipment_recommendation": "Ensure ventilator and ICU bed availability",
        }

    @staticmethod
    def detect_operational_bottlenecks(hospital_id) -> list:
        bottlenecks = []

        wards = Ward.objects.filter(hospital_id=hospital_id, is_active=True)
        for ward in wards:
            beds = Bed.objects.filter(ward=ward)
            total = beds.count()
            if total == 0:
                continue
            occupied = beds.filter(occupancy_status=Bed.Status.OCCUPIED).count()
            util = occupied / total * 100
            if util >= 90:
                bottlenecks.append({
                    "type": "ward_capacity",
                    "severity": "critical" if util >= 95 else "warning",
                    "ward_id": ward.id,
                    "ward_name": ward.ward_name,
                    "utilization_pct": round(util, 1),
                    "detail": f"{ward.ward_name} at {round(util, 1)}% capacity",
                    "recommended_action": "Consider patient redistribution or surge capacity activation",
                })

        wait_time_wards = Ward.objects.filter(
            hospital_id=hospital_id, is_active=True,
            metadata__has_key="avg_wait_minutes",
        ).values("id", "ward_name", "metadata")

        for w in wait_time_wards:
            avg_wait = w.get("metadata", {}).get("avg_wait_minutes", 0)
            if avg_wait > 60:
                bottlenecks.append({
                    "type": "wait_time",
                    "severity": "critical" if avg_wait > 120 else "warning",
                    "ward_id": w["id"],
                    "ward_name": w["ward_name"],
                    "avg_wait_minutes": avg_wait,
                    "detail": f"Average wait time {avg_wait} minutes in {w['ward_name']}",
                    "recommended_action": "Triage optimization and additional staff during peak hours",
                })

        return bottlenecks

    @staticmethod
    def generate_optimization_recommendations(hospital_id) -> list:
        recommendations = []

        wards = Ward.objects.filter(hospital_id=hospital_id, is_active=True)
        for ward in wards:
            beds = Bed.objects.filter(ward=ward)
            total = beds.count()
            if total == 0:
                continue
            occupied = beds.filter(occupancy_status=Bed.Status.OCCUPIED).count()
            util = occupied / total * 100

            if util > 85:
                recommendations.append({
                    "area": f"capacity_{ward.ward_name}",
                    "priority": "high",
                    "recommendation": f"Expand {ward.ward_name} capacity or redistribute load",
                    "impact": "reduced wait times and improved patient outcomes",
                    "current_utilization": round(util, 1),
                })

        recent_alerts = OperationalAlert.objects.filter(
            hospital_id=hospital_id,
            created_at__gte=timezone.now() - timedelta(days=7),
        ).count()

        if recent_alerts > 20:
            recommendations.append({
                "area": "alert_management",
                "priority": "medium",
                "recommendation": "Investigate root causes of operational alerts",
                "impact": "reduced alert fatigue and faster response to critical issues",
                "alert_count_7d": recent_alerts,
            })

        return recommendations

    @staticmethod
    def get_hospital_efficiency_score(hospital_id) -> dict:
        wards = Ward.objects.filter(hospital_id=hospital_id, is_active=True)
        total_beds = 0
        total_occupied = 0

        for ward in wards:
            beds = Bed.objects.filter(ward=ward)
            total_beds += beds.count()
            total_occupied += beds.filter(occupancy_status=Bed.Status.OCCUPIED).count()

        utilization_rate = total_occupied / total_beds if total_beds > 0 else 0
        utilization_score = max(0, 100 - abs(0.75 - utilization_rate) * 100)

        alert_penalty = OperationalAlert.objects.filter(
            hospital_id=hospital_id,
            created_at__gte=timezone.now() - timedelta(days=7),
            severity__in=["critical", "emergency"],
        ).count() * 5

        score = max(0, min(100, round(utilization_score - alert_penalty, 1)))

        return {
            "hospital_id": hospital_id,
            "efficiency_score": score,
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 50 else "D",
            "utilization_rate_pct": round(utilization_rate * 100, 1),
            "alert_penalty": alert_penalty,
            "recommendations": OperationalIntelligenceService.generate_optimization_recommendations(hospital_id),
        }

    @staticmethod
    def create_operational_alert(category, severity, title, description, hospital=None, metric_name="", metric_value=None, threshold=None, action="") -> OperationalAlert:
        alert = OperationalAlert.objects.create(
            category=category,
            severity=severity,
            hospital=hospital,
            title=title,
            description=description,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold_value=threshold,
            source_service="operational_intelligence",
            recommended_action=action,
        )

        EventBus.emit(
            event_source="system",
            event_type=f"operational_alert.{category}.{severity}",
            data={
                "alert_id": alert.id,
                "category": category,
                "severity": severity,
                "title": title,
                "hospital_id": hospital.id if hospital else None,
            },
            aggregate_type="OperationalAlert",
            aggregate_id=str(alert.id),
        )

        return alert
