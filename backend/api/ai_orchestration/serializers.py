from rest_framework import serializers
from core.models import AIModelRegistry


class AIModelRegistrySerializer(serializers.ModelSerializer):
    approved_by_name = serializers.SerializerMethodField()
    model_type_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AIModelRegistry
        fields = [
            "id", "model_name", "model_version", "model_type", "model_type_display",
            "description", "status", "status_display", "model_artifact_path",
            "input_schema", "output_schema", "performance_metrics",
            "explainability_config", "governance_approval", "approved_by",
            "approved_by_name", "approved_at", "audit_trail", "metadata",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["approved_at", "created_at", "updated_at"]

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.first_name} {obj.approved_by.last_name}"
        return ""

    def get_model_type_display(self, obj):
        return obj.get_model_type_display() if hasattr(obj, "get_model_type_display") else obj.model_type


class UpdateModelStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=AIModelRegistry.ModelStatus.choices)
    governance_approval = serializers.BooleanField(required=False)
