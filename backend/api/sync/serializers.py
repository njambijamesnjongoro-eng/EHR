from rest_framework import serializers
from core.models import SyncQueue, SyncLog


class SyncQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncQueue
        fields = "__all__"
        read_only_fields = ["status", "error_message", "retry_count", "server_timestamp", "processed_at"]


class SyncBatchSerializer(serializers.Serializer):
    items = SyncQueueSerializer(many=True)
    device_id = serializers.CharField(required=False, allow_blank=True)


class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = "__all__"
        read_only_fields = ["completed_at"]


class SyncStatusSerializer(serializers.Serializer):
    pending_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    last_sync = serializers.DateTimeField(allow_null=True)
