from celery import shared_task
from core.models import Hospital
from services.analytics_service import AnalyticsService


@shared_task
def generate_hospital_snapshot(hospital_id):
    try:
        hospital = Hospital.objects.get(id=hospital_id)
        data = AnalyticsService.hospital_dashboard(hospital)
        # Cache to Redis or database for fast access
        return f"Snapshot generated for {hospital.hospital_code}"
    except Hospital.DoesNotExist:
        return f"Hospital {hospital_id} not found"


@shared_task
def generate_daily_snapshots():
    hospitals = Hospital.objects.filter(is_active=True)
    for hospital in hospitals:
        generate_hospital_snapshot.delay(hospital.id)
    return f"Queued snapshots for {hospitals.count()} hospitals"
