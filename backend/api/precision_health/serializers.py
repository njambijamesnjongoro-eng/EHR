from rest_framework import serializers
from core.models import HealthRiskProfile


class HealthRiskProfileSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    risk_category_display = serializers.CharField(source="get_risk_category_display", read_only=True)

    class Meta:
        model = HealthRiskProfile
        fields = [
            "id", "patient", "patient_name", "risk_category", "risk_category_display",
            "risk_score", "risk_level", "contributing_factors", "protective_factors",
            "longitudinal_trend", "last_assessed_at", "assessment_model",
            "metadata", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "last_assessed_at", "risk_score", "risk_level"]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else ""


class RiskAssessmentSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    risk_category = serializers.ChoiceField(choices=HealthRiskProfile.RiskCategory.choices)


class HighRiskQuerySerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=HealthRiskProfile.RiskCategory.choices, required=False, allow_blank=True)
    hospital_id = serializers.IntegerField(required=False, allow_null=True)
    limit = serializers.IntegerField(default=50, required=False)
