from rest_framework import serializers
from core.models import PublicHealthMetric, PublicHealthForecast


class PublicHealthMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHealthMetric
        fields = [
            "id", "metric_category", "county", "sub_county",
            "disease_code", "disease_name", "metric_value", "metric_unit",
            "population_base", "sample_size",
            "confidence_interval_low", "confidence_interval_high",
            "period_start", "period_end", "created_at",
        ]
        read_only_fields = ["created_at"]


class DiseasePrevalenceSerializer(serializers.Serializer):
    period_days = serializers.IntegerField(default=90)
    diseases = serializers.ListField(child=serializers.DictField())


class OutbreakSignalSerializer(serializers.Serializer):
    icd_code = serializers.CharField()
    diagnosis_name = serializers.CharField()
    recent_count = serializers.IntegerField()
    baseline_count = serializers.IntegerField()
    ratio = serializers.FloatField()
    signal_strength = serializers.CharField()


class CountyHealthSerializer(serializers.Serializer):
    disease_code = serializers.CharField(required=False, allow_blank=True)
    period_days = serializers.IntegerField(default=30)


class PublicHealthForecastSerializer(serializers.ModelSerializer):
    forecast_category_display = serializers.CharField(source="get_forecast_category_display", read_only=True)
    trend_direction_display = serializers.CharField(source="get_trend_direction_display", read_only=True)

    class Meta:
        model = PublicHealthForecast
        fields = [
            "id", "forecast_category", "forecast_category_display", "county",
            "disease_code", "disease_name", "forecast_date", "predicted_cases",
            "predicted_lower", "predicted_upper", "confidence_level", "model_name",
            "seasonality_factor", "trend_direction", "trend_direction_display",
            "risk_level", "metadata", "created_at",
        ]
        read_only_fields = ["created_at"]
