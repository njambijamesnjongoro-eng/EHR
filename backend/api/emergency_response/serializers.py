from rest_framework import serializers
from core.models import EmergencyResponseEvent


class EmergencyResponseEventSerializer(serializers.ModelSerializer):
    incident_commander_name = serializers.SerializerMethodField()
    emergency_type_display = serializers.CharField(source="get_emergency_type_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EmergencyResponseEvent
        fields = [
            "id", "emergency_type", "emergency_type_display", "severity", "severity_display",
            "status", "status_display", "title", "description", "location_region",
            "affected_counties", "affected_population", "estimated_casualties",
            "hospital_capacity_impact", "resource_needs", "responding_units",
            "coordination_center", "incident_commander", "incident_commander_name",
            "escalated_at", "contained_at", "resolved_at", "lessons_learned",
            "metadata", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_incident_commander_name(self, obj):
        if obj.incident_commander:
            return f"{obj.incident_commander.first_name} {obj.incident_commander.last_name}"
        return ""


class UpdateStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=EmergencyResponseEvent.Status.choices)
