from rest_framework import serializers
from core.models import CitizenHealthProfile, WearableDevice, DeviceReading


class CitizenHealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CitizenHealthProfile
        fields = [
            "id", "patient", "preferred_language", "emergency_contacts",
            "allergies_summary", "chronic_conditions_summary",
            "medication_summary", "vaccination_summary",
            "notification_preferences", "consent_settings",
            "portal_enabled", "last_portal_login",
            "created_at", "updated_at",
        ]
        read_only_fields = ["last_portal_login", "created_at", "updated_at"]


class ProfileUpdateSerializer(serializers.Serializer):
    preferred_language = serializers.CharField(max_length=10, required=False)
    emergency_contacts = serializers.JSONField(required=False)
    notification_preferences = serializers.JSONField(required=False)
    allergies_summary = serializers.CharField(required=False, allow_blank=True)
    chronic_conditions_summary = serializers.CharField(required=False, allow_blank=True)


class HealthShareSerializer(serializers.Serializer):
    recipient_email = serializers.EmailField()
    data_types = serializers.ListField(child=serializers.CharField(max_length=50))
    expiry_hours = serializers.IntegerField(default=24, required=False)
