from datetime import timedelta

from django.db.models import Count, Avg, Sum
from django.utils import timezone

from core.models import (
    PredictiveMetric, InfrastructureEvent, PredictiveAlert,
    SystemHealthMetric, SyncQueue, Hospital,
)
from events.event_bus import EventBus


class AutonomousOperationsService:
    """Autonomous healthcare operations — predictive load balancing, anomaly detection, resource forecasting."""

    @staticmethod
    def record_prediction(metric_category, metric_name, predicted_value, *,
                          hospital=None, county="", confidence_lower=None, confidence_upper=None,
                          horizon=7, model="", features=None) -> PredictiveMetric:
        from datetime import date
        metric = PredictiveMetric.objects.create(
            metric_category=metric_category,
            hospital=hospital,
            county=county,
            metric_name=metric_name,
            predicted_value=predicted_value,
            confidence_interval_lower=confidence_lower,
            confidence_interval_upper=confidence_upper,
            prediction_date=date.today() + timedelta(days=horizon),
            forecast_horizon_days=horizon,
            model_name=model,
            features_used=features or [],
        )

        EventBus.emit_system(
            event_type=f"prediction.{metric_category}",
            data={
                "metric_id": metric.id,
                "name": metric_name,
                "value": predicted_value,
                "horizon": horizon,
            },
            aggregate_type="PredictiveMetric",
            aggregate_id=str(metric.id),
        )

        return metric

    @staticmethod
    def log_infrastructure_event(event_type, severity, message, *,
                                  service="", host="", metrics=None, auto_action="") -> InfrastructureEvent:
        event = InfrastructureEvent.objects.create(
            event_type=event_type,
            severity=severity,
            service_name=service,
            host_name=host,
            message=message,
            metric_data=metrics or {},
            auto_action_taken=auto_action,
            occurred_at=timezone.now(),
        )

        if severity in ("error", "critical"):
            PredictiveAlert.objects.create(
                category=PredictiveAlert.AlertCategory.ANOMALY,
                severity=severity,
                title=f"Infrastructure: {event_type}",
                description=message,
                predicted_at=timezone.now(),
                confidence_score=0.9,
                metadata={"event_id": event.id, "service": service},
            )

        return event

    @staticmethod
    def analyze_operational_anomalies(hours: int = 1) -> list:
        anomalies = []
        since = timezone.now() - timedelta(hours=hours)

        pending = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.PENDING).count()
        if pending > 200:
            anomalies.append({
                "type": "sync_backlog",
                "severity": "warning",
                "value": pending,
                "message": f"Sync queue backlog: {pending} items pending",
            })

        infra_errors = InfrastructureEvent.objects.filter(
            occurred_at__gte=since,
            severity__in=["error", "critical"],
        ).count()
        if infra_errors > 5:
            anomalies.append({
                "type": "infrastructure_errors",
                "severity": "critical" if infra_errors > 20 else "warning",
                "value": infra_errors,
                "message": f"{infra_errors} infrastructure errors in last hour",
            })

        return anomalies

    @staticmethod
    def resource_forecast(hospital_id: int, days: int = 30) -> dict:
        from core.models import Bed, Ward, Admission
        total_beds = Bed.objects.filter(ward__hospital_id=hospital_id, is_active=True).count()
        occupied = Admission.objects.filter(hospital_id=hospital_id, status="active").count()
        available = total_beds - occupied

        recent_admissions = Admission.objects.filter(
            hospital_id=hospital_id,
            admission_date__gte=timezone.now() - timedelta(days=30),
        ).count()
        avg_daily = recent_admissions / 30

        return {
            "hospital_id": hospital_id,
            "forecast_horizon_days": days,
            "current_beds": {"total": total_beds, "occupied": occupied, "available": available},
            "avg_daily_admissions": round(avg_daily, 1),
            "projected_occupancy_in_days": {
                str(i): round(occupied + (avg_daily * i * 0.6), 0)
                for i in [1, 3, 7, 14, 30]
            },
            "capacity_risk": "critical" if occupied / total_beds > 0.9 else "high" if occupied / total_beds > 0.75 else "moderate",
        }

    @staticmethod
    def operational_insights(hospital_id: int) -> dict:
        from django.db.models import Count
        from core.models import Ward

        wards = Ward.objects.filter(hospital_id=hospital_id, is_active=True)
        ward_stats = []
        for ward in wards:
            beds = ward.beds.all()
            total = beds.count()
            occ = beds.filter(occupancy_status="occupied").count()
            ward_stats.append({
                "ward": ward.ward_name,
                "type": ward.ward_type,
                "beds": total,
                "occupied": occ,
                "utilization": round(occ / total * 100, 1) if total > 0 else 0,
            })

        return {
            "hospital_id": hospital_id,
            "wards": ward_stats,
            "overall_utilization": round(
                sum(w["occupied"] for w in ward_stats) / sum(w["beds"] for w in ward_stats) * 100, 1
            ) if sum(w["beds"] for w in ward_stats) > 0 else 0,
            "total_beds": sum(w["beds"] for w in ward_stats),
            "total_occupied": sum(w["occupied"] for w in ward_stats),
        }

    @staticmethod
    def automated_scaling_recommendation() -> list:
        recommendations = []

        pending_sync = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.PENDING).count()
        if pending_sync > 500:
            recommendations.append({
                "component": "sync_worker",
                "action": "scale_up",
                "reason": f"Sync queue at {pending_sync} items",
                "priority": "high",
            })

        return recommendations
