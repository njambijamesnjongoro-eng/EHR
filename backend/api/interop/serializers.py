from rest_framework import serializers
from core.models import ExternalSystem, EnterpriseAuditEvent


class ExternalSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalSystem
        fields = [
            "id", "system_name", "system_type", "hospital", "base_url",
            "api_key_hash", "auth_type", "is_active", "config",
            "last_sync_at", "last_sync_status", "created_at", "updated_at",
        ]
        read_only_fields = ["api_key_hash", "last_sync_at", "last_sync_status", "created_at", "updated_at"]


class ExternalSystemRegisterSerializer(serializers.Serializer):
    system_name = serializers.CharField(max_length=200)
    system_type = serializers.ChoiceField(choices=ExternalSystem.SystemType.choices)
    base_url = serializers.URLField(max_length=500)
    auth_type = serializers.ChoiceField(choices=[
        ("api_key", "API Key"),
        ("oauth2", "OAuth 2.0"),
        ("basic", "Basic Auth"),
        ("mutual_tls", "Mutual TLS"),
        ("none", "No Auth"),
    ], default="api_key")
    config = serializers.JSONField(default=dict, required=False)


class FHIRConversionSerializer(serializers.Serializer):
    resource_type = serializers.ChoiceField(choices=[
        "Patient", "Encounter", "Observation", "MedicationRequest", "DiagnosticReport",
    ])
    data = serializers.JSONField()


class IntegrationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseAuditEvent
        fields = [
            "id", "event_type", "hospital", "user", "resource_type",
            "resource_id", "action", "description", "severity", "created_at",
        ]
