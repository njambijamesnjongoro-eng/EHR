from rest_framework import serializers
from core.models import EpidemicAlert, PublicHealthForecast


class EpidemicAlertSerializer(serializers.ModelSerializer):
    alert_level_display = serializers.CharField(source="get_alert_level_display", read_only=True)
    alert_source_display = serializers.CharField(source="get_alert_source_display", read_only=True)

    class Meta:
        model = EpidemicAlert
        fields = [
            "id", "alert_level", "alert_level_display", "alert_source", "alert_source_display",
            "disease_code", "disease_name", "county", "sub_county", "location_point",
            "confirmed_cases", "suspected_cases", "reported_deaths", "attack_rate",
            "doubling_time_days", "r0_estimate", "affected_population", "signal_strength",
            "triggered_by_event", "recommended_actions", "is_active", "resolved_at",
            "metadata", "detected_at", "created_at",
        ]
        read_only_fields = ["created_at", "resolved_at", "detected_at"]


class PublicHealthForecastSerializer(serializers.ModelSerializer):
    forecast_category_display = serializers.CharField(source="get_forecast_category_display", read_only=True)
    trend_direction_display = serializers.CharField(source="get_trend_direction_display", read_only=True)
    risk_level_display = serializers.CharField(source="get_risk_level_display", read_only=True)

    class Meta:
        model = PublicHealthForecast
        fields = [
            "id", "forecast_category", "forecast_category_display", "county",
            "disease_code", "disease_name", "forecast_date", "predicted_cases",
            "predicted_lower", "predicted_upper", "confidence_level", "model_name",
            "seasonality_factor", "trend_direction", "trend_direction_display",
            "risk_level", "risk_level_display", "metadata", "created_at",
        ]
        read_only_fields = ["created_at"]
