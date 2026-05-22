from rest_framework import serializers
from core.models import Ward, Bed, Admission


class WardSerializer(serializers.ModelSerializer):
    available_beds = serializers.IntegerField(read_only=True)
    occupied_beds = serializers.IntegerField(read_only=True)
    total_beds = serializers.SerializerMethodField()

    class Meta:
        model = Ward
        fields = [
            "id", "ward_name", "ward_type", "capacity",
            "available_beds", "occupied_beds", "total_beds",
            "description", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_total_beds(self, obj):
        return obj.beds.count()


class BedSerializer(serializers.ModelSerializer):
    ward_name = serializers.SerializerMethodField()

    class Meta:
        model = Bed
        fields = ["id", "ward", "ward_name", "bed_number", "occupancy_status"]

    def get_ward_name(self, obj):
        return obj.ward.ward_name if obj.ward else None


class AdmissionListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_health_id = serializers.SerializerMethodField()
    ward_name = serializers.SerializerMethodField()
    bed_number = serializers.SerializerMethodField()
    admitted_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Admission
        fields = [
            "id", "patient", "patient_name", "patient_health_id",
            "ward", "ward_name", "bed", "bed_number",
            "admission_reason", "admission_date", "discharge_date",
            "status", "admitted_by", "admitted_by_name", "discharge_notes",
        ]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_patient_health_id(self, obj):
        return obj.patient.health_id if obj.patient else None

    def get_ward_name(self, obj):
        return obj.ward.ward_name if obj.ward else None

    def get_bed_number(self, obj):
        return obj.bed.bed_number if obj.bed else None

    def get_admitted_by_name(self, obj):
        if obj.admitted_by:
            return obj.admitted_by.get_full_name() or obj.admitted_by.email
        return None


class AdmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admission
        fields = [
            "patient", "ward", "bed", "admission_reason",
        ]

    def validate(self, attrs):
        bed = attrs.get("bed")
        if bed and bed.occupancy_status != Bed.Status.AVAILABLE:
            raise serializers.ValidationError("Bed is not available")
        patient = attrs.get("patient")
        if patient and Admission.objects.filter(
            patient=patient, status=Admission.Status.ACTIVE
        ).exists():
            raise serializers.ValidationError("Patient has an active admission")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["admitted_by"] = request.user
        bed = validated_data.get("bed")
        if bed:
            bed.occupancy_status = Bed.Status.OCCUPIED
            bed.save(update_fields=["occupancy_status"])
        return super().create(validated_data)


class AdmissionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admission
        fields = ["discharge_notes"]

    def update(self, instance, validated_data):
        request = self.context.get("request")
        from django.utils import timezone
        instance.status = Admission.Status.DISCHARGED
        instance.discharge_date = timezone.now()
        instance.discharged_by = request.user if request else None
        instance.discharge_notes = validated_data.get("discharge_notes", "")
        if instance.bed:
            instance.bed.occupancy_status = Bed.Status.AVAILABLE
            instance.bed.save(update_fields=["occupancy_status"])
        instance.save()
        return instance
