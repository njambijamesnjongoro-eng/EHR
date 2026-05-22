import json
from datetime import datetime

from django.db import models, transaction
from django.utils import timezone

from core.models import SyncQueue, SyncLog, EnterpriseAuditEvent


class SyncService:
    """Offline-first synchronization engine with conflict resolution."""

    @staticmethod
    def enqueue(hospital, resource_type, resource_id, action, payload, device_id="", client_timestamp=None):
        SyncQueue.objects.create(
            hospital=hospital,
            device_id=device_id,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else "",
            action=action,
            payload=payload,
            status=SyncQueue.SyncStatus.PENDING,
            client_timestamp=client_timestamp or timezone.now(),
        )

    @staticmethod
    @transaction.atomic
    def process_queue(hospital, device_id="", batch_size=50):
        items = SyncQueue.objects.filter(
            hospital=hospital,
            status=SyncQueue.SyncStatus.PENDING,
            retry_count__lt=models.F("max_retries"),
        ).order_by("client_timestamp")[:batch_size]

        processed = 0
        failed = 0
        start = timezone.now()

        for item in items:
            try:
                SyncService._process_item(item)
                item.status = SyncQueue.SyncStatus.COMPLETED
                item.processed_at = timezone.now()
                item.save(update_fields=["status", "processed_at"])
                processed += 1
            except Exception as e:
                item.retry_count += 1
                item.error_message = str(e)
                if item.retry_count >= item.max_retries:
                    item.status = SyncQueue.SyncStatus.FAILED
                item.save(update_fields=["retry_count", "error_message", "status"])
                failed += 1

        duration = int((timezone.now() - start).total_seconds() * 1000)

        if processed or failed:
            SyncLog.objects.create(
                hospital=hospital,
                device_id=device_id,
                items_processed=processed,
                items_failed=failed,
                duration_ms=duration,
                status="success" if failed == 0 else "partial" if processed > 0 else "failed",
            )

        return {"processed": processed, "failed": failed, "duration_ms": duration}

    @staticmethod
    def _process_item(item: SyncQueue):
        from django.apps import apps

        model = apps.get_model("core", item.resource_type)
        payload = item.payload

        if item.action == SyncQueue.SyncAction.CREATE:
            model.objects.create(**payload)

        elif item.action == SyncQueue.SyncAction.UPDATE:
            instance = model.objects.get(id=item.resource_id)
            for key, value in payload.items():
                setattr(instance, key, value)
            instance.save()

        elif item.action == SyncQueue.SyncAction.DELETE:
            model.objects.filter(id=item.resource_id).delete()

    @staticmethod
    def resolve_conflict(item: SyncQueue, resolution: dict):
        """Manually resolve a conflicted sync item."""
        item.payload = resolution
        item.status = SyncQueue.SyncStatus.PENDING
        item.conflict_resolution = "manual"
        item.retry_count = 0
        item.save()

    @staticmethod
    def get_pending_count(hospital) -> int:
        return SyncQueue.objects.filter(
            hospital=hospital,
            status=SyncQueue.SyncStatus.PENDING,
        ).count()



