import time
from django.db import connection
from django.core.cache import cache
from django.utils import timezone

from core.models import SystemHealthMetric, SyncQueue, SecurityEvent


def record_system_metrics():
    """Record system health metrics to the database.

    Called periodically by Celery beat.
    """
    now = timezone.now()

    # Sync queue depth
    pending = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.PENDING).count()
    SystemHealthMetric.objects.create(
        metric_type=SystemHealthMetric.MetricType.QUEUE_DEPTH,
        value=pending,
        unit="items",
        tags={"queue": "sync"},
        recorded_at=now,
    )

    failed = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.FAILED).count()
    SystemHealthMetric.objects.create(
        metric_type=SystemHealthMetric.MetricType.QUEUE_DEPTH,
        value=failed,
        unit="items",
        tags={"queue": "sync_failed"},
        recorded_at=now,
    )

    # Security events (last 24h)
    from datetime import timedelta
    recent_sec = SecurityEvent.objects.filter(
        detected_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    SystemHealthMetric.objects.create(
        metric_type=SystemHealthMetric.MetricType.API_REQUESTS,
        value=recent_sec,
        unit="events",
        tags={"type": "security_24h"},
        recorded_at=now,
    )

    # Cache hit ratio (approximate)
    try:
        cache.set("metric_test", 1, 10)
        cache.get("metric_test")
        SystemHealthMetric.objects.create(
            metric_type=SystemHealthMetric.MetricType.CACHE_HIT_RATIO,
            value=1.0,
            unit="ratio",
            recorded_at=now,
        )
    except Exception:
        SystemHealthMetric.objects.create(
            metric_type=SystemHealthMetric.MetricType.CACHE_HIT_RATIO,
            value=0.0,
            unit="ratio",
            recorded_at=now,
        )

    # Active user count
    from core.models import User
    active = User.objects.filter(is_active=True).count()
    SystemHealthMetric.objects.create(
        metric_type=SystemHealthMetric.MetricType.ACTIVE_USERS,
        value=active,
        unit="users",
        recorded_at=now,
    )

    return {
        "metrics_recorded": 6,
        "pending_sync": pending,
        "active_users": active,
    }
