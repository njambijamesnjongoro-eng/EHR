from rest_framework import serializers
from core.models import ImagingRequest, ImagingResult


class ImagingRequestListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    requested_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ImagingRequest
        fields = [
            "id", "visit", "patient", "patient_name",
            "imaging_type", "priority", "status",
            "clinical_history", "region_examined",
            "requested_by", "requested_by_name",
            "requested_at", "created_at",
        ]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_requested_by_name(self, obj):
        if obj.requested_by:
            return obj.requested_by.get_full_name() or obj.requested_by.email
        return None


class ImagingRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingRequest
        fields = [
            "visit", "patient", "imaging_type",
            "priority", "clinical_history", "region_examined",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["requested_by"] = request.user
        return super().create(validated_data)


class ImagingResultSerializer(serializers.ModelSerializer):
    imaging_type = serializers.SerializerMethodField()
    radiologist_name = serializers.SerializerMethodField()

    class Meta:
        model = ImagingResult
        fields = [
            "id", "imaging_request", "imaging_type",
            "patient", "findings", "impression", "report",
            "radiologist", "radiologist_name",
            "image_file", "report_file", "is_abnormal",
            "result_at", "created_at",
        ]
        read_only_fields = ["id", "radiologist", "result_at"]

    def get_imaging_type(self, obj):
        return obj.imaging_request.get_imaging_type_display() if obj.imaging_request else None

    def get_radiologist_name(self, obj):
        if obj.radiologist:
            return obj.radiologist.get_full_name() or obj.radiologist.email
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["radiologist"] = request.user
        img_request = validated_data.get("imaging_request")
        if img_request:
            validated_data["patient"] = img_request.patient
            img_request.status = ImagingRequest.Status.COMPLETED
            img_request.save(update_fields=["status"])
        return super().create(validated_data)
