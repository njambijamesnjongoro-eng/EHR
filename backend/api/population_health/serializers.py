from rest_framework import serializers
from core.models import PopulationHealthInsight, PredictiveForecast


class PopulationHealthInsightSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = PopulationHealthInsight
        fields = [
            "id", "category", "category_display", "county", "sub_county", "region",
            "indicator_name", "indicator_value", "population_base",
            "confidence_interval_low", "confidence_interval_high", "percentile_rank",
            "trend_direction", "comparison_national", "comparison_regional",
            "period_start", "period_end", "metadata", "is_anonymized", "created_at",
        ]
        read_only_fields = ["created_at"]


class PredictiveForecastSerializer(serializers.ModelSerializer):
    domain_display = serializers.CharField(source="get_domain_display", read_only=True)
    hospital_name = serializers.SerializerMethodField()

    class Meta:
        model = PredictiveForecast
        fields = [
            "id", "domain", "domain_display", "hospital", "hospital_name",
            "county", "region", "metric_name", "predicted_value", "actual_value",
            "predicted_lower", "predicted_upper", "confidence_level",
            "forecast_date", "forecast_horizon_days", "trend_direction",
            "seasonality_factor", "model_name", "model_accuracy",
            "features_used", "metadata", "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_hospital_name(self, obj):
        return obj.hospital.hospital_name if obj.hospital else ""


class RecordInsightSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=PopulationHealthInsight.InsightCategory.choices)
    county = serializers.CharField(max_length=100)
    sub_county = serializers.CharField(max_length=100, required=False, allow_blank=True)
    region = serializers.CharField(max_length=200, required=False, allow_blank=True)
    indicator_name = serializers.CharField(max_length=300)
    indicator_value = serializers.FloatField()
    population_base = serializers.IntegerField(default=0)
    period_start = serializers.DateField()
    period_end = serializers.DateField()


class RecordForecastSerializer(serializers.Serializer):
    domain = serializers.ChoiceField(choices=PredictiveForecast.ForecastDomain.choices)
    metric_name = serializers.CharField(max_length=200)
    predicted_value = serializers.FloatField()
    forecast_date = serializers.DateField()
    county = serializers.CharField(max_length=100, required=False, allow_blank=True)
    region = serializers.CharField(max_length=200, required=False, allow_blank=True)
    forecast_horizon_days = serializers.IntegerField(default=7)
