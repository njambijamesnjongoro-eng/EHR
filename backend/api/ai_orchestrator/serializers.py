from rest_framework import serializers
from core.models import AIRecommendation


class AIRecommendationSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    accepted_by_name = serializers.SerializerMethodField()
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    recommendation_type_display = serializers.CharField(source="get_recommendation_type_display", read_only=True)

    class Meta:
        model = AIRecommendation
        fields = [
            "id", "recommendation_type", "recommendation_type_display", "priority", "priority_display",
            "patient", "patient_name", "visit", "title", "recommendation_text",
            "clinical_rationale", "supporting_evidence", "confidence_score",
            "source_service", "is_accepted", "accepted_by", "accepted_by_name",
            "accepted_at", "rejection_reason", "metadata", "created_at",
        ]
        read_only_fields = ["created_at", "accepted_at", "is_accepted"]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else ""

    def get_accepted_by_name(self, obj):
        if obj.accepted_by:
            return f"{obj.accepted_by.first_name} {obj.accepted_by.last_name}"
        return ""


class AIRecommendationActionSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class GenerateRecommendationSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    visit_id = serializers.IntegerField(required=False, allow_null=True)
    recommendation_type = serializers.ChoiceField(choices=["clinical", "preventive"], default="clinical")


class WorkflowOptimizationSerializer(serializers.Serializer):
    hospital_id = serializers.IntegerField()
