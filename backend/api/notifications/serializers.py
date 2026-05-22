from rest_framework import serializers
from core.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "recipient", "patient", "category",
            "title", "message", "is_read", "link", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
