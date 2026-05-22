from rest_framework import serializers
from core.models import ConsentLog, EnterpriseAuditEvent


class ConsentLogSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    granted_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ConsentLog
        fields = [
            "id", "patient", "patient_name", "consent_type", "status",
            "granted_by", "granted_by_name", "granted_at",
            "expires_at", "revoked_at", "revocation_reason",
            "consent_version", "metadata",
        ]
        read_only_fields = ["granted_at", "revoked_at", "status"]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else ""

    def get_granted_by_name(self, obj):
        if obj.granted_by:
            return f"{obj.granted_by.first_name} {obj.granted_by.last_name}"
        return ""


class ConsentGrantSerializer(serializers.Serializer):
    consent_type = serializers.ChoiceField(choices=ConsentLog.ConsentType.choices)
    consent_version = serializers.CharField(default="1.0", max_length=20)
    expires_days = serializers.IntegerField(default=None, allow_null=True, required=False)
    metadata = serializers.JSONField(default=dict, required=False)


class ConsentRevokeSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class EnterpriseAuditEventSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = EnterpriseAuditEvent
        fields = [
            "id", "event_type", "hospital", "user", "user_name",
            "actor_type", "resource_type", "resource_id", "action",
            "description", "ip_address", "user_agent", "metadata",
            "severity", "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return ""


class AuditReportSerializer(serializers.Serializer):
    period_days = serializers.IntegerField()
    total_events = serializers.IntegerField()
    by_event_type = serializers.DictField(child=serializers.IntegerField())
    by_severity = serializers.DictField(child=serializers.IntegerField())
    by_user = serializers.DictField(child=serializers.IntegerField())
    security_events = serializers.IntegerField()
