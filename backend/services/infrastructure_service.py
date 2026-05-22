from datetime import timedelta

from django.db.models import Count, Avg, Max, Min
from django.utils import timezone

from core.models import (
    SystemHealthMetric, SyncQueue, SecurityEvent,
    EnterpriseAuditEvent,
)
from events.event_bus import EventBus


class InfrastructureOptimizationService:
    """Self-monitoring, autonomous infrastructure optimization."""

    @staticmethod
    def assess_system_health() -> dict:
        since_1h = timezone.now() - timedelta(hours=1)
        since_24h = timezone.now() - timedelta(hours=24)

        metrics = {
            "database": InfrastructureOptimizationService._check_database(),
            "cache": InfrastructureOptimizationService._check_cache(),
            "sync_queue": InfrastructureOptimizationService._check_sync_queue(),
            "security": InfrastructureOptimizationService._check_security(since_24h),
            "performance": InfrastructureOptimizationService._check_performance(since_1h),
            "errors": InfrastructureOptimizationService._check_errors(since_24h),
        }

        overall = "healthy"
        degraded_count = sum(1 for c in metrics.values() if c.get("status") == "degraded")
        critical_count = sum(1 for c in metrics.values() if c.get("status") == "critical")

        if critical_count > 0:
            overall = "critical"
        elif degraded_count > 1:
            overall = "degraded"

        return {
            "overall_status": overall,
            "checks": metrics,
            "timestamp": timezone.now().isoformat(),
            "degraded_count": degraded_count,
            "critical_count": critical_count,
        }

    @staticmethod
    def _check_database() -> dict:
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"status": "healthy", "message": "Database reachable"}
        except Exception as e:
            return {"status": "critical", "message": str(e)}

    @staticmethod
    def _check_cache() -> dict:
        try:
            from django.core.cache import cache
            cache.set("infra_health", 1, 5)
            return {"status": "healthy", "message": "Cache reachable"}
        except Exception as e:
            return {"status": "degraded", "message": str(e)}

    @staticmethod
    def _check_sync_queue() -> dict:
        pending = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.PENDING).count()
        failed = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.FAILED).count()

        if failed > 50:
            return {"status": "critical", "pending": pending, "failed": failed}
        if pending > 500:
            return {"status": "degraded", "pending": pending, "failed": failed}
        return {"status": "healthy", "pending": pending, "failed": failed}

    @staticmethod
    def _check_security(since) -> dict:
        critical_events = SecurityEvent.objects.filter(
            detected_at__gte=since,
            severity__in=["high", "critical"],
        ).count()

        if critical_events > 10:
            return {"status": "critical", "critical_events_24h": critical_events}
        if critical_events > 3:
            return {"status": "degraded", "critical_events_24h": critical_events}
        return {"status": "healthy", "critical_events_24h": critical_events}

    @staticmethod
    def _check_performance(since) -> dict:
        latency = SystemHealthMetric.objects.filter(
            metric_type=SystemHealthMetric.MetricType.API_LATENCY,
            recorded_at__gte=since,
        ).aggregate(avg=Avg("value"), max=Max("value"))

        avg_latency = latency.get("avg") or 0

        if avg_latency > 2000:
            return {"status": "degraded", "avg_latency_ms": round(avg_latency, 0)}
        return {"status": "healthy", "avg_latency_ms": round(avg_latency, 0)}

    @staticmethod
    def _check_errors(since) -> dict:
        error_rate = SystemHealthMetric.objects.filter(
            metric_type=SystemHealthMetric.MetricType.ERROR_RATE,
            recorded_at__gte=since,
        ).aggregate(avg=Avg("value"))

        rate = error_rate.get("avg") or 0
        if rate > 0.1:
            return {"status": "degraded", "error_rate": round(rate, 4)}
        return {"status": "healthy", "error_rate": round(rate, 4)}

    @staticmethod
    def get_optimization_recommendations() -> list:
        recommendations = []

        pending = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.PENDING).count()
        if pending > 200:
            recommendations.append({
                "area": "sync_queue",
                "priority": "high",
                "recommendation": "Increase sync worker count or batch size",
                "current_value": pending,
            })

        failed = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.FAILED).count()
        if failed > 20:
            recommendations.append({
                "area": "sync_queue",
                "priority": "high",
                "recommendation": "Investigate and clear failed sync items",
                "current_value": failed,
            })

        latency = SystemHealthMetric.objects.filter(
            metric_type=SystemHealthMetric.MetricType.API_LATENCY,
            recorded_at__gte=timezone.now() - timedelta(hours=1),
        ).aggregate(avg=Avg("value"))

        if latency.get("avg") and latency["avg"] > 1000:
            recommendations.append({
                "area": "performance",
                "priority": "medium",
                "recommendation": "High API latency detected. Consider scaling API workers or optimizing queries.",
                "current_value": round(latency["avg"], 0),
            })

        return recommendations

    @staticmethod
    def run_self_healing() -> dict:
        actions = []

        failed = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.FAILED, retry_count__lt=3)
        if failed.exists():
            count = failed.count()
            failed.update(status=SyncQueue.SyncStatus.PENDING)
            actions.append(f"Re-queued {count} failed sync items for retry")

        return {"actions_taken": actions, "timestamp": timezone.now().isoformat()}

    @staticmethod
    def record_infrastructure_metric(metric_type, value, unit="", tags=None):
        return SystemHealthMetric.objects.create(
            metric_type=metric_type,
            value=value,
            unit=unit,
            tags=tags or {},
        )
