from rest_framework import serializers
from core.models import WearableDevice, DeviceReading


class WearableDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WearableDevice
        fields = [
            "id", "patient", "device_type", "device_name", "manufacturer",
            "model_number", "serial_number", "firmware_version",
            "is_active", "is_verified", "pairing_token", "config",
            "last_sync_at", "created_at", "updated_at",
        ]
        read_only_fields = ["is_verified", "pairing_token", "last_sync_at", "created_at", "updated_at"]


class WearableRegisterSerializer(serializers.Serializer):
    device_type = serializers.ChoiceField(choices=WearableDevice.DeviceType.choices)
    device_name = serializers.CharField(max_length=200)
    manufacturer = serializers.CharField(max_length=200, required=False)
    model_number = serializers.CharField(max_length=100, required=False)
    serial_number = serializers.CharField(max_length=200)
    firmware_version = serializers.CharField(max_length=50, required=False)
    config = serializers.JSONField(default=dict, required=False)


class DeviceReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceReading
        fields = [
            "id", "device", "patient", "reading_type", "value", "unit",
            "metadata", "recorded_at", "ingested_at", "is_abnormal",
        ]
        read_only_fields = ["ingested_at", "is_abnormal"]


class DeviceReadingIngestSerializer(serializers.Serializer):
    device_id = serializers.IntegerField()
    patient_id = serializers.IntegerField()
    reading_type = serializers.ChoiceField(choices=DeviceReading.ReadingType.choices)
    value = serializers.FloatField()
    unit = serializers.CharField(max_length=50, required=False, default="")
    recorded_at = serializers.DateTimeField(required=False)
    metadata = serializers.JSONField(required=False, default=dict)


class DeviceReadingBulkSerializer(serializers.Serializer):
    readings = DeviceReadingIngestSerializer(many=True)


class DeviceVerifySerializer(serializers.Serializer):
    pairing_token = serializers.CharField(max_length=255)
