import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("ehr")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "process-sync-queue": {
        "task": "tasks.sync_tasks.process_all_queues",
        "schedule": 60.0,  # every 60 seconds
    },
    "generate-analytics-cache": {
        "task": "tasks.analytics_tasks.generate_daily_snapshots",
        "schedule": 3600.0,  # every hour
    },
    "cleanup-expired-access": {
        "task": "tasks.maintenance_tasks.cleanup_expired_cross_hospital_access",
        "schedule": 86400.0,  # daily
    },
    "cleanup-old-audit-logs": {
        "task": "tasks.maintenance_tasks.cleanup_old_audit_logs",
        "schedule": 86400.0,
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
