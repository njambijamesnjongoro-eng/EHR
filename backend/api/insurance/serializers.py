from rest_framework import serializers
from core.models import InsuranceProfile, InsuranceClaim


class InsuranceProfileSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_health_id = serializers.CharField(source="patient.health_id", read_only=True)

    class Meta:
        model = InsuranceProfile
        fields = "__all__"
        read_only_fields = ["verified", "verification_data", "created_at", "updated_at"]


class InsuranceProfileListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = InsuranceProfile
        fields = ["id", "patient_name", "provider", "policy_number", "coverage_type", "is_active", "verified", "effective_from", "effective_to"]


class InsuranceClaimSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="insurance_profile.patient.full_name", read_only=True)
    policy_number = serializers.CharField(source="insurance_profile.policy_number", read_only=True)

    class Meta:
        model = InsuranceClaim
        fields = "__all__"
        read_only_fields = ["claim_number", "status", "approved_amount", "response_data", "submitted_at", "responded_at", "created_at", "updated_at"]


class InsuranceClaimActionSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)


class ClaimSubmissionSerializer(serializers.Serializer):
    insurance_profile = serializers.IntegerField()
    invoice = serializers.IntegerField(required=False, allow_null=True)
    claim_data = serializers.JSONField()
