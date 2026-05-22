from rest_framework import serializers
from core.models import LabRequest, LabResult


class LabRequestListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    requested_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LabRequest
        fields = [
            "id",
            "visit",
            "patient",
            "patient_name",
            "test_name",
            "priority",
            "status",
            "requested_by",
            "requested_by_name",
            "requested_at",
            "created_at",
        ]
        read_only_fields = ["id", "requested_by", "requested_at", "status"]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_requested_by_name(self, obj):
        if obj.requested_by:
            return obj.requested_by.get_full_name() or obj.requested_by.email
        return None


class LabRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabRequest
        fields = [
            "visit",
            "patient",
            "test_name",
            "priority",
            "clinical_notes",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["requested_by"] = request.user
        return super().create(validated_data)


class LabRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabRequest
        fields = ["status"]


class LabResultSerializer(serializers.ModelSerializer):
    test_name = serializers.SerializerMethodField()
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LabResult
        fields = [
            "id",
            "lab_request",
            "test_name",
            "patient",
            "result_data",
            "result_text",
            "remarks",
            "is_abnormal",
            "file_attachment",
            "performed_by",
            "performed_by_name",
            "result_at",
            "created_at",
        ]
        read_only_fields = ["id", "performed_by", "result_at"]

    def get_test_name(self, obj):
        return obj.lab_request.test_name if obj.lab_request else None

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.get_full_name() or obj.performed_by.email
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["performed_by"] = request.user

        lab_request = validated_data.get("lab_request")
        if lab_request:
            validated_data["patient"] = lab_request.patient
            lab_request.status = LabRequest.Status.COMPLETED
            lab_request.save(update_fields=["status"])

        return super().create(validated_data)
