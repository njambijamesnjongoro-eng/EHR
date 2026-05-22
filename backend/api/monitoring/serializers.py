from rest_framework import serializers
from core.models import SystemHealthMetric, EventStreamLog, InfrastructureTwin


class SystemHealthMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemHealthMetric
        fields = [
            "id", "metric_type", "hospital", "value", "unit", "tags", "recorded_at",
        ]
        read_only_fields = ["recorded_at"]


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    checks = serializers.DictField(child=serializers.DictField())
    timestamp = serializers.DateTimeField()


class SystemHealthDashboardSerializer(serializers.Serializer):
    queue_depth = serializers.IntegerField()
    active_users = serializers.IntegerField()
    cache_hit_ratio = serializers.FloatField()
    recent_latency_avg = serializers.FloatField()
    error_rate_24h = serializers.FloatField()
    recent_metrics = SystemHealthMetricSerializer(many=True)


class EventStreamLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventStreamLog
        fields = [
            "id", "event_id", "event_source", "event_type", "event_version",
            "aggregate_type", "aggregate_id", "data", "metadata",
            "correlation_id", "causation_id", "occurred_at",
        ]
        read_only_fields = []


class InfrastructureTwinMonitorSerializer(serializers.ModelSerializer):
    hospital_name = serializers.SerializerMethodField()
    twin_type_display = serializers.CharField(source="get_twin_type_display", read_only=True)
    simulation_status_display = serializers.CharField(source="get_simulation_status_display", read_only=True)

    class Meta:
        model = InfrastructureTwin
        fields = [
            "id", "twin_type", "twin_type_display", "name", "hospital", "hospital_name",
            "region", "description", "simulation_status", "simulation_status_display",
            "last_simulated_at", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_hospital_name(self, obj):
        return obj.hospital.hospital_name if obj.hospital else ""
