from datetime import timedelta
from collections import defaultdict

from django.db.models import Avg, Count, Max, Min
from django.utils import timezone

from core.models import SmartHospitalMetric, DeviceTelemetryEvent, SmartHospitalDevice, Hospital
from events.event_bus import EventBus


class SmartAutomationService:
    """Smart hospital automation — metric monitoring, device telemetry, anomaly detection, and dashboard analytics."""

    @staticmethod
    def record_hospital_metric(hospital, metric_category, metric_name, metric_value, unit="", ward=None, threshold_warning=None, threshold_critical=None) -> SmartHospitalMetric:
        is_alert = False
        if threshold_critical is not None and metric_value >= threshold_critical:
            is_alert = True
        elif threshold_warning is not None and metric_value >= threshold_warning:
            is_alert = True

        metric = SmartHospitalMetric.objects.create(
            hospital=hospital,
            ward=ward,
            metric_category=metric_category,
            metric_name=metric_name,
            metric_value=metric_value,
            unit=unit,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical,
            is_alert=is_alert,
            recorded_at=timezone.now(),
        )

        if is_alert:
            EventBus.emit(
                event_source="system",
                event_type=f"smart_metric.alert.{metric_category}",
                data={
                    "metric_id": metric.id,
                    "hospital_id": hospital.id,
                    "category": metric_category,
                    "metric_name": metric_name,
                    "value": metric_value,
                    "threshold_warning": threshold_warning,
                    "threshold_critical": threshold_critical,
                },
                aggregate_type="SmartHospitalMetric",
                aggregate_id=str(metric.id),
            )

        return metric

    @staticmethod
    def get_hospital_metrics_dashboard(hospital_id, hours=24) -> dict:
        since = timezone.now() - timedelta(hours=hours)

        metrics = SmartHospitalMetric.objects.filter(
            hospital_id=hospital_id,
            recorded_at__gte=since,
        )

        by_category = defaultdict(list)
        for m in metrics:
            by_category[m.metric_category].append({
                "id": m.id,
                "name": m.metric_name,
                "value": m.metric_value,
                "unit": m.unit,
                "ward_id": m.ward_id,
                "is_alert": m.is_alert,
                "recorded_at": m.recorded_at.isoformat(),
            })

        alerts = metrics.filter(is_alert=True).count()

        return {
            "hospital_id": hospital_id,
            "period_hours": hours,
            "total_metrics": metrics.count(),
            "active_alerts": alerts,
            "by_category": dict(by_category),
            "categories": list(by_category.keys()),
        }

    @staticmethod
    def detect_metric_anomalies(hospital_id, category=None) -> list:
        since = timezone.now() - timedelta(hours=24)

        qs = SmartHospitalMetric.objects.filter(
            hospital_id=hospital_id,
            recorded_at__gte=since,
            is_alert=True,
        )
        if category:
            qs = qs.filter(metric_category=category)

        anomalies = []
        for metric in qs.select_related("ward")[:50]:
            threshold_info = {}
            if metric.threshold_critical is not None and metric.metric_value >= metric.threshold_critical:
                threshold_info["type"] = "critical"
                threshold_info["threshold"] = metric.threshold_critical
            elif metric.threshold_warning is not None and metric.metric_value >= metric.threshold_warning:
                threshold_info["type"] = "warning"
                threshold_info["threshold"] = metric.threshold_warning

            anomalies.append({
                "metric_id": metric.id,
                "category": metric.metric_category,
                "metric_name": metric.metric_name,
                "value": metric.metric_value,
                "unit": metric.unit,
                "ward": metric.ward.ward_name if metric.ward else None,
                "threshold": threshold_info,
                "recorded_at": metric.recorded_at.isoformat(),
            })

        return anomalies

    @staticmethod
    def record_device_telemetry(device_id, hospital_id, telemetry_type, metric_name, metric_value, **kwargs) -> DeviceTelemetryEvent:
        try:
            device = SmartHospitalDevice.objects.get(id=device_id)
        except SmartHospitalDevice.DoesNotExist:
            raise ValueError(f"Device {device_id} not found")

        telemetry = DeviceTelemetryEvent.objects.create(
            device=device,
            hospital_id=hospital_id,
            telemetry_type=telemetry_type,
            metric_name=metric_name,
            metric_value=metric_value,
            unit=kwargs.get("unit", ""),
            latitude=kwargs.get("latitude"),
            longitude=kwargs.get("longitude"),
            signal_strength=kwargs.get("signal_strength"),
            battery_level=kwargs.get("battery_level"),
            firmware_version=device.firmware_version if hasattr(device, "firmware_version") else "",
            payload=kwargs.get("payload", {}),
            is_abnormal=kwargs.get("is_abnormal", False),
            recorded_at=timezone.now(),
        )

        if telemetry.is_abnormal:
            EventBus.emit(
                event_source="integration",
                event_type=f"device_telemetry.abnormal.{telemetry_type}",
                data={
                    "telemetry_id": telemetry.id,
                    "device_id": device_id,
                    "hospital_id": hospital_id,
                    "metric_name": metric_name,
                    "value": metric_value,
                    "is_abnormal": True,
                },
                aggregate_type="DeviceTelemetryEvent",
                aggregate_id=str(telemetry.id),
            )

        return telemetry

    @staticmethod
    def get_device_telemetry_analytics(device_id, hours=24) -> dict:
        since = timezone.now() - timedelta(hours=hours)

        events = DeviceTelemetryEvent.objects.filter(
            device_id=device_id,
            recorded_at__gte=since,
        )

        by_type = defaultdict(list)
        for e in events:
            by_type[e.telemetry_type].append({
                "id": e.id,
                "metric_name": e.metric_name,
                "value": e.metric_value,
                "unit": e.unit,
                "is_abnormal": e.is_abnormal,
                "recorded_at": e.recorded_at.isoformat(),
            })

        return {
            "device_id": device_id,
            "period_hours": hours,
            "total_readings": events.count(),
            "abnormal_readings": events.filter(is_abnormal=True).count(),
            "by_type": dict(by_type),
            "summary": {
                "avg_signal": events.aggregate(avg=Avg("signal_strength"))["avg"],
                "avg_battery": events.aggregate(avg=Avg("battery_level"))["avg"],
            },
        }

    @staticmethod
    def get_hospital_telemetry_summary(hospital_id) -> dict:
        since = timezone.now() - timedelta(hours=24)

        events = DeviceTelemetryEvent.objects.filter(
            hospital_id=hospital_id,
            recorded_at__gte=since,
        )

        by_device = events.values("device_id").annotate(
            total=Count("id"),
            abnormal=Count("id", filter=__import__("django.db.models", fromlist=["Q"]).Q(is_abnormal=True)),
        )

        return {
            "hospital_id": hospital_id,
            "period_hours": 24,
            "total_telemetry_events": events.count(),
            "abnormal_events": events.filter(is_abnormal=True).count(),
            "active_devices": events.values("device_id").distinct().count(),
            "by_type": dict(events.values_list("telemetry_type").annotate(count=Count("id"))),
            "device_summary": list(by_device),
        }
