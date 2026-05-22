from rest_framework import serializers
from core.models import AIInsight


class AIInsightSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AIInsight
        fields = [
            "id", "insight_type", "patient", "patient_name", "visit",
            "title", "summary", "details", "confidence", "confidence_score",
            "source_service", "is_reviewed", "reviewed_by", "reviewed_by_name",
            "reviewed_at", "clinical_action_taken", "created_at",
        ]
        read_only_fields = ["created_at", "reviewed_at", "confidence", "is_reviewed"]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else ""

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return f"{obj.reviewed_by.first_name} {obj.reviewed_by.last_name}"
        return ""


class AIInsightReviewSerializer(serializers.Serializer):
    action_taken = serializers.CharField(max_length=500, required=False, allow_blank=True)


class RiskAssessmentSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()


class MedicationCheckSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
