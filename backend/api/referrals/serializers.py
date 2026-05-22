from rest_framework import serializers
from core.models import Referral, ReferralDocument


class ReferralSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_health_id = serializers.CharField(source="patient.health_id", read_only=True)
    referring_hospital_name = serializers.CharField(source="referring_hospital.hospital_name", read_only=True)
    receiving_hospital_name = serializers.CharField(source="receiving_hospital.hospital_name", read_only=True)
    referring_doctor_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source="receiving_department.department_name", read_only=True)

    class Meta:
        model = Referral
        fields = "__all__"
        read_only_fields = ["status", "responded_by", "responded_at", "completed_at", "created_at", "updated_at"]

    def get_referring_doctor_name(self, obj):
        if obj.referring_doctor:
            return obj.referring_doctor.get_full_name()
        return ""


class ReferralCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = [
            "patient", "receiving_hospital", "receiving_department",
            "priority", "clinical_summary", "reason_for_referral", "referral_notes",
        ]


class ReferralActionSerializer(serializers.Serializer):
    response_notes = serializers.CharField(required=False, allow_blank=True)


class ReferralDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralDocument
        fields = "__all__"
        read_only_fields = ["created_at"]
