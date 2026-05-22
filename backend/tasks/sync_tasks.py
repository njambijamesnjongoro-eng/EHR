from celery import shared_task
from core.models import Hospital
from services.sync_service import SyncService


@shared_task
def process_hospital_queue(hospital_id):
    try:
        hospital = Hospital.objects.get(id=hospital_id)
        result = SyncService.process_queue(hospital)
        return f"Hospital {hospital.hospital_code}: {result}"
    except Hospital.DoesNotExist:
        return f"Hospital {hospital_id} not found"


@shared_task
def process_all_queues():
    hospitals = Hospital.objects.filter(is_active=True)
    results = []
    for hospital in hospitals:
        result = process_hospital_queue.delay(hospital.id)
        results.append(f"{hospital.hospital_code}: task {result.id}")
    return results
