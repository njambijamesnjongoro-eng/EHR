from rest_framework import serializers
from core.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_name",
            "action",
            "resource_type",
            "resource_id",
            "description",
            "ip_address",
            "request_path",
            "response_status",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.email
        return "System"
