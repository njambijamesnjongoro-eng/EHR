import time
from django.http import JsonResponse
from django.db import connection, models
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from core.models import (
    SystemHealthMetric, SyncQueue, SecurityEvent,
    Hospital, Patient, User,
)


def prometheus_metrics(request):
    """Exposes Prometheus-compatible metrics endpoint.

    GET /api/monitoring/metrics/
    """
    from django.db.models import Count

    metrics = []

    # Active users
    active_users = User.objects.filter(is_active=True).count()
    metrics.append(f"# HELP ehr_active_users Total active users")
    metrics.append(f"# TYPE ehr_active_users gauge")
    metrics.append(f"ehr_active_users {active_users}")

    # Total patients
    total_patients = Patient.objects.filter(is_active=True).count()
    metrics.append(f"# HELP ehr_total_patients Total active patients")
    metrics.append(f"# TYPE ehr_total_patients gauge")
    metrics.append(f"ehr_total_patients {total_patients}")

    # Hospitals
    total_hospitals = Hospital.objects.filter(is_active=True).count()
    metrics.append(f"# HELP ehr_total_hospitals Total active hospitals")
    metrics.append(f"# TYPE ehr_total_hospitals gauge")
    metrics.append(f"ehr_total_hospitals {total_hospitals}")

    # Sync queue depth
    pending_sync = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.PENDING).count()
    metrics.append(f"# HELP ehr_sync_queue_pending Pending sync items")
    metrics.append(f"# TYPE ehr_sync_queue_pending gauge")
    metrics.append(f"ehr_sync_queue_pending {pending_sync}")

    failed_sync = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.FAILED).count()
    metrics.append(f"# HELP ehr_sync_queue_failed Failed sync items")
    metrics.append(f"# TYPE ehr_sync_queue_failed gauge")
    metrics.append(f"ehr_sync_queue_failed {failed_sync}")

    # Security events (last 24h)
    from datetime import timedelta
    recent_sec = SecurityEvent.objects.filter(
        detected_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    metrics.append(f"# HELP ehr_security_events_24h Security events in last 24 hours")
    metrics.append(f"# TYPE ehr_security_events_24h gauge")
    metrics.append(f"ehr_security_events_24h {recent_sec}")

    # Critical security events (last 24h)
    critical_sec = SecurityEvent.objects.filter(
        detected_at__gte=timezone.now() - timedelta(hours=24),
        severity__in=["high", "critical"],
    ).count()
    metrics.append(f"# HELP ehr_critical_security_events_24h Critical security events in 24h")
    metrics.append(f"# TYPE ehr_critical_security_events_24h gauge")
    metrics.append(f"ehr_critical_security_events_24h {critical_sec}")

    # Cache status
    try:
        cache.set("ehr_health_check", 1, 10)
        cache_ok = 1
    except Exception:
        cache_ok = 0
    metrics.append(f"# HELP ehr_cache_status Redis cache status (1=ok)")
    metrics.append(f"# TYPE ehr_cache_status gauge")
    metrics.append(f"ehr_cache_status {cache_ok}")

    # Database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ok = 1
    except Exception:
        db_ok = 0
    metrics.append(f"# HELP ehr_db_status Database status (1=ok)")
    metrics.append(f"# TYPE ehr_db_status gauge")
    metrics.append(f"ehr_db_status {db_ok}")

    # Queue length by hospital
    hospital_counts = (
        SyncQueue.objects.filter(status=SyncQueue.SyncStatus.PENDING)
        .values("hospital__hospital_code")
        .annotate(count=models.Count("id"))
    )
    for hc in hospital_counts:
        code = hc["hospital__hospital_code"] or "unknown"
        metrics.append(f'ehr_hospital_sync_pending{{hospital="{code}"}} {hc["count"]}')

    return JsonResponse({"metrics": "\n".join(metrics)}, status=200)


def health_check(request):
    """Comprehensive health check endpoint.

    GET /api/monitoring/health/
    """
    from django.db.models import Count
    from datetime import timedelta

    checks = {}

    # Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            table_count = cursor.fetchone()[0]
        checks["database"] = {"status": "healthy", "tables": table_count}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Cache
    try:
        cache.set("health_check", 1, 5)
        cache.get("health_check")
        checks["cache"] = {"status": "healthy"}
    except Exception as e:
        checks["cache"] = {"status": "unhealthy", "error": str(e)}

    # Celery (check if workers are responsive)
    # Future: celery ping check

    # Sync queue
    pending = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.PENDING).count()
    checks["sync_queue"] = {"pending": pending, "status": "healthy" if pending < 1000 else "degraded"}

    # Recent errors
    recent_errors = SecurityEvent.objects.filter(
        severity="critical",
        detected_at__gte=timezone.now() - timedelta(hours=1),
    ).count()
    checks["recent_critical_events"] = {"count": recent_errors, "status": "healthy" if recent_errors == 0 else "degraded"}

    overall = all(c.get("status") == "healthy" for c in checks.values())
    status_code = 200 if overall else 503

    return JsonResponse({
        "status": "healthy" if overall else "degraded",
        "checks": checks,
        "timestamp": timezone.now().isoformat(),
    }, status=status_code)



