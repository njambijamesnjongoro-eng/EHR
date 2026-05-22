from datetime import timedelta
from collections import defaultdict

from django.db.models import Count, Avg, Q
from django.utils import timezone

from core.models import (
    PredictiveAlert, Patient, Visit, Admission, Bed, Ward,
    Hospital, DeviceReading, SyncQueue,
)
from events.event_bus import EventBus


class PredictiveAnalyticsService:
    """Predictive healthcare analytics and forecasting."""

    @staticmethod
    def create_alert(category, severity, title, description, *, hospital=None, patient=None,
                     confidence_score=0.0, suggested_action="", affected_entity_type="",
                     affected_entity_id="", metadata=None) -> PredictiveAlert:
        alert = PredictiveAlert.objects.create(
            category=category,
            severity=severity,
            title=title,
            description=description,
            predicted_at=timezone.now(),
            confidence_score=confidence_score,
            hospital=hospital,
            patient=patient,
            suggested_action=suggested_action,
            affected_entity_type=affected_entity_type,
            affected_entity_id=affected_entity_id,
            metadata=metadata or {},
        )

        EventBus.emit_system(
            event_type=f"predictive_alert.{category}",
            data={
                "alert_id": alert.id,
                "category": category,
                "severity": severity,
                "title": title,
                "hospital_id": hospital.id if hospital else None,
                "patient_id": patient.id if patient else None,
            },
            aggregate_type="PredictiveAlert",
            aggregate_id=str(alert.id),
        )

        return alert

    @staticmethod
    def predict_hospital_load(hospital_id: int, days_ahead: int = 7) -> dict:
        """Predict hospital capacity and patient load."""
        today = timezone.now()
        past_30 = today - timedelta(days=30)

        daily_admissions = Admission.objects.filter(
            hospital_id=hospital_id,
            admission_date__gte=past_30,
        ).extra({"date": "date(admission_date)"}).values("date").annotate(
            count=Count("id"),
        ).order_by("date")

        daily_discharges = Admission.objects.filter(
            hospital_id=hospital_id,
            discharge_date__gte=past_30,
        ).extra({"date": "date(discharge_date)"}).values("date").annotate(
            count=Count("id"),
        ).order_by("date")

        avg_daily_admissions = sum(d["count"] for d in daily_admissions) / 30 if daily_admissions else 0
        avg_daily_discharges = sum(d["count"] for d in daily_discharges) / 30 if daily_discharges else 0

        current_occupancy = Admission.objects.filter(
            hospital_id=hospital_id, status=Admission.AdmissionStatus.ACTIVE,
        ).count()

        total_beds = Bed.objects.filter(
            ward__hospital_id=hospital_id, occupancy_status__in=["available", "occupied"],
        ).count()

        bed_utilization = (current_occupancy / total_beds * 100) if total_beds > 0 else 0

        predicted_occupancy = current_occupancy + (avg_daily_admissions - avg_daily_discharges) * days_ahead

        return {
            "hospital_id": hospital_id,
            "current_occupancy": current_occupancy,
            "total_beds": total_beds,
            "bed_utilization_pct": round(bed_utilization, 1),
            "avg_daily_admissions": round(avg_daily_admissions, 1),
            "avg_daily_discharges": round(avg_daily_discharges, 1),
            "predicted_occupancy_in_days": {
                str(i): round(current_occupancy + (avg_daily_admissions - avg_daily_discharges) * i, 0)
                for i in range(1, days_ahead + 1)
            },
            "risk_level": "critical" if predicted_occupancy > total_beds * 0.9
            else "high" if predicted_occupancy > total_beds * 0.75
            else "moderate" if predicted_occupancy > total_beds * 0.6
            else "normal",
        }

    @staticmethod
    def predict_patient_flow(hospital_id: int, days_ahead: int = 30) -> dict:
        today = timezone.now()
        past = today - timedelta(days=90)

        weekly_visits = Visit.objects.filter(
            hospital_id=hospital_id,
            visit_date__gte=past,
        ).extra({"week": "date_trunc('week', visit_date)"}).values("week").annotate(
            count=Count("id"),
        ).order_by("week")

        counts = [w["count"] for w in weekly_visits]
        trend = 0
        if len(counts) >= 2:
            trend = (counts[-1] - counts[-2]) / max(counts[-2], 1)

        return {
            "hospital_id": hospital_id,
            "period_days": days_ahead,
            "weekly_trend_pct": round(trend * 100, 1),
            "projected_weekly_visits": max(0, round(counts[-1] * (1 + trend))) if counts else 0,
            "historical_weekly_avg": round(sum(counts) / len(counts), 1) if counts else 0,
        }

    @staticmethod
    def detect_system_anomalies() -> list:
        alerts = []
        since = timezone.now() - timedelta(hours=1)

        pending_sync = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.PENDING).count()
        if pending_sync > 100:
            alerts.append(PredictiveAnalyticsService.create_alert(
                category=PredictiveAlert.AlertCategory.ANOMALY,
                severity=PredictiveAlert.Severity.WARNING,
                title="High Sync Queue Depth",
                description=f"{pending_sync} items pending in sync queue",
                confidence_score=0.7,
                affected_entity_type="SyncQueue",
                metadata={"pending_count": pending_sync},
            ))

        failed_sync = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.FAILED).count()
        if failed_sync > 10:
            alerts.append(PredictiveAnalyticsService.create_alert(
                category=PredictiveAlert.AlertCategory.ANOMALY,
                severity=PredictiveAlert.Severity.WARNING,
                title="High Sync Failure Count",
                description=f"{failed_sync} items failed in sync queue",
                confidence_score=0.8,
                affected_entity_type="SyncQueue",
                metadata={"failed_count": failed_sync},
            ))

        return alerts

    @staticmethod
    def acknowledge_alert(alert_id: int, user) -> PredictiveAlert:
        alert = PredictiveAlert.objects.get(id=alert_id)
        alert.status = PredictiveAlert.Status.ACKNOWLEDGED
        alert.acknowledged_by = user
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=["status", "acknowledged_by", "acknowledged_at"])
        return alert

    @staticmethod
    def resolve_alert(alert_id: int, user) -> PredictiveAlert:
        alert = PredictiveAlert.objects.get(id=alert_id)
        alert.status = PredictiveAlert.Status.RESOLVED
        alert.resolved_by = user
        alert.resolved_at = timezone.now()
        alert.save(update_fields=["status", "resolved_by", "resolved_at"])
        return alert

    @staticmethod
    def active_alerts(hospital_id: int = None, category: str = None) -> list:
        qs = PredictiveAlert.objects.filter(status=PredictiveAlert.Status.ACTIVE)
        if hospital_id:
            qs = qs.filter(hospital_id=hospital_id)
        if category:
            qs = qs.filter(category=category)
        return qs.order_by("-predicted_at")[:50]
