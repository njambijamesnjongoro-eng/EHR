from rest_framework import serializers
from core.models import SmartHospitalDevice, SmartHospitalMetric, SmartDeviceEvent


class SmartHospitalDeviceSerializer(serializers.ModelSerializer):
    hospital_name = serializers.SerializerMethodField()
    ward_name = serializers.SerializerMethodField()

    class Meta:
        model = SmartHospitalDevice
        fields = [
            "id", "hospital", "hospital_name", "ward", "ward_name", "bed",
            "device_category", "device_name", "serial_number",
            "ip_address", "mac_address", "firmware_version",
            "is_online", "is_active", "config",
            "last_heartbeat", "created_at", "updated_at",
        ]
        read_only_fields = ["last_heartbeat", "created_at", "updated_at"]

    def get_hospital_name(self, obj):
        return obj.hospital.hospital_name if obj.hospital else ""

    def get_ward_name(self, obj):
        return obj.ward.ward_name if obj.ward else ""


class SmartHospitalRegisterSerializer(serializers.Serializer):
    device_category = serializers.ChoiceField(choices=SmartHospitalDevice.DeviceCategory.choices)
    device_name = serializers.CharField(max_length=200)
    serial_number = serializers.CharField(max_length=200)
    ward_id = serializers.IntegerField(required=False, allow_null=True)
    bed_id = serializers.IntegerField(required=False, allow_null=True)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    mac_address = serializers.CharField(max_length=50, required=False)
    firmware_version = serializers.CharField(max_length=50, required=False)
    config = serializers.JSONField(default=dict, required=False)


class HeartbeatSerializer(serializers.Serializer):
    device_id = serializers.IntegerField()


class BedOccupancySummarySerializer(serializers.Serializer):
    ward_name = serializers.CharField()
    ward_type = serializers.CharField()
    total_beds = serializers.IntegerField()
    occupied = serializers.IntegerField()
    available = serializers.IntegerField()
    utilization_pct = serializers.FloatField()


class SmartDeviceEventSerializer(serializers.ModelSerializer):
    device_name = serializers.SerializerMethodField()
    ward_name = serializers.SerializerMethodField()
    event_category_display = serializers.CharField(source="get_event_category_display", read_only=True)

    class Meta:
        model = SmartDeviceEvent
        fields = [
            "id", "device", "device_name", "hospital", "ward", "ward_name",
            "event_category", "event_category_display", "event_type", "value", "unit",
            "payload", "severity", "is_processed", "occurred_at", "processed_at", "created_at",
        ]
        read_only_fields = ["created_at", "processed_at", "is_processed"]

    def get_device_name(self, obj):
        return obj.device.device_name if obj.device else ""

    def get_ward_name(self, obj):
        return obj.ward.ward_name if obj.ward else ""


class DeviceIngestSerializer(serializers.Serializer):
    device_id = serializers.IntegerField()
    event_category = serializers.ChoiceField(choices=SmartDeviceEvent.EventCategory.choices)
    event_type = serializers.CharField(max_length=100)
    value = serializers.FloatField(required=False, allow_null=True)
    payload = serializers.JSONField(default=dict, required=False)
    severity = serializers.ChoiceField(choices=["info", "warning", "critical", "emergency"], default="info")


class PatientFlowQuerySerializer(serializers.Serializer):
    hospital_id = serializers.IntegerField(required=False)
    days = serializers.IntegerField(default=7, required=False)


class SmartHospitalMetricSerializer(serializers.ModelSerializer):
    hospital_name = serializers.SerializerMethodField()
    ward_name = serializers.SerializerMethodField()
    metric_category_display = serializers.CharField(source="get_metric_category_display", read_only=True)

    class Meta:
        model = SmartHospitalMetric
        fields = [
            "id", "hospital", "hospital_name", "ward", "ward_name",
            "metric_category", "metric_category_display", "metric_name", "metric_value",
            "unit", "threshold_warning", "threshold_critical", "is_alert",
            "recorded_at", "metadata", "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_hospital_name(self, obj):
        return obj.hospital.hospital_name if obj.hospital else ""

    def get_ward_name(self, obj):
        return obj.ward.ward_name if obj.ward else ""


