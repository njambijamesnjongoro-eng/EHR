from datetime import timedelta

from celery import shared_task
from django.db import models
from django.utils import timezone

from core.models import CrossHospitalAccess, EnterpriseAuditEvent, SyncQueue
from django.conf import settings


@shared_task
def cleanup_expired_cross_hospital_access():
    cutoff = timezone.now()
    expired = CrossHospitalAccess.objects.filter(
        expires_at__lt=cutoff, is_authorized=True
    )
    count = expired.count()
    expired.update(is_authorized=False)
    return f"Expired {count} access grants"


@shared_task
def cleanup_old_audit_logs():
    retention_days = getattr(settings, "AUDIT_LOG_RETENTION_DAYS", 365)
    cutoff = timezone.now() - timedelta(days=retention_days)
    old = EnterpriseAuditEvent.objects.filter(created_at__lt=cutoff)
    count = old.count()
    old.delete()
    return f"Cleaned {count} old audit events"


@shared_task
def retry_failed_sync_items():
    failed = SyncQueue.objects.filter(
        status=SyncQueue.SyncStatus.FAILED,
        retry_count__lt=models.F("max_retries"),
    )
    count = failed.count()
    failed.update(status=SyncQueue.SyncStatus.PENDING)
    return f"Re-queued {count} failed sync items"


