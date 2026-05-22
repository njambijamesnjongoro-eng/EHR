from rest_framework import serializers
from core.models import SecurityEvent, DeviceFingerprint, MFAToken, InfrastructureEvent, OperationalAlert


class SecurityEventSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = SecurityEvent
        fields = [
            "id", "category", "severity", "user", "user_email", "hospital",
            "ip_address", "user_agent", "device_fingerprint", "risk_score",
            "description", "metadata", "detected_at", "resolved", "resolved_by", "resolved_at",
        ]
        read_only_fields = ["detected_at", "resolved_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data.setdefault("user", request.user)
        return super().create(validated_data)


class SecurityEventResolveSerializer(serializers.Serializer):
    resolved = serializers.BooleanField()


class DeviceFingerprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceFingerprint
        fields = [
            "id", "user", "fingerprint_hash", "device_name", "device_type",
            "os", "browser", "ip_address", "is_trusted",
            "last_seen_at", "first_seen_at", "risk_count",
        ]
        read_only_fields = ["fingerprint_hash", "last_seen_at", "first_seen_at", "risk_count"]


class MFATokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = MFAToken
        fields = ["id", "user", "token_type", "secret", "is_active", "verified_at", "created_at"]
        read_only_fields = ["secret", "verified_at", "created_at"]


class MFASetupResponseSerializer(serializers.Serializer):
    qr_code_url = serializers.URLField(read_only=True)
    secret = serializers.CharField(read_only=True)
    backup_codes = serializers.ListField(child=serializers.CharField(), read_only=True)


class MFATokenCodeSerializer(serializers.Serializer):
    token_code = serializers.CharField(max_length=64)


class RiskDashboardSerializer(serializers.Serializer):
    total_high_risk = serializers.IntegerField()
    critical_events_24h = serializers.IntegerField()
    unique_users_flagged = serializers.IntegerField()
    recent_unresolved = SecurityEventSerializer(many=True)


class InfrastructureEventMonitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureEvent
        fields = [
            "id", "event_type", "severity", "service_name", "host_name",
            "message", "auto_action_taken", "auto_action_success",
            "resolved", "occurred_at", "created_at",
        ]
        read_only_fields = ["created_at"]


class OperationalAlertSerializer(serializers.ModelSerializer):
    hospital_name = serializers.SerializerMethodField()
    acknowledged_by_name = serializers.SerializerMethodField()
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)

    class Meta:
        model = OperationalAlert
        fields = [
            "id", "category", "category_display", "severity", "severity_display",
            "hospital", "hospital_name", "title", "description", "metric_name",
            "metric_value", "threshold_value", "source_service", "recommended_action",
            "is_acknowledged", "acknowledged_by", "acknowledged_by_name",
            "acknowledged_at", "is_resolved", "resolved_at", "metadata", "created_at",
        ]
        read_only_fields = ["acknowledged_at", "resolved_at", "created_at"]

    def get_hospital_name(self, obj):
        return obj.hospital.hospital_name if obj.hospital else ""

    def get_acknowledged_by_name(self, obj):
        if obj.acknowledged_by:
            return f"{obj.acknowledged_by.first_name} {obj.acknowledged_by.last_name}"
        return ""
