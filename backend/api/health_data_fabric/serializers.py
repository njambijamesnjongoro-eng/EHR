from rest_framework import serializers
from core.models import InfrastructureEvent, EventStreamLog, PredictiveMetric


class InfrastructureEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)

    class Meta:
        model = InfrastructureEvent
        fields = [
            "id", "event_type", "event_type_display", "severity", "service_name",
            "host_name", "message", "metric_data", "auto_action_taken",
            "auto_action_success", "resolved", "resolved_at", "metadata",
            "occurred_at", "created_at",
        ]
        read_only_fields = ["created_at", "resolved_at"]


class EventStreamLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventStreamLog
        fields = [
            "id", "event_id", "event_source", "event_type", "event_version",
            "aggregate_type", "aggregate_id", "data", "metadata",
            "correlation_id", "causation_id", "occurred_at",
        ]
        read_only_fields = ["event_id", "occurred_at"]


class PredictiveMetricSerializer(serializers.ModelSerializer):
    metric_category_display = serializers.CharField(source="get_metric_category_display", read_only=True)

    class Meta:
        model = PredictiveMetric
        fields = [
            "id", "metric_category", "metric_category_display", "hospital", "county",
            "metric_name", "predicted_value", "actual_value",
            "confidence_interval_lower", "confidence_interval_upper",
            "prediction_date", "forecast_horizon_days", "model_name",
            "model_accuracy", "features_used", "metadata", "created_at",
        ]
        read_only_fields = ["created_at"]
