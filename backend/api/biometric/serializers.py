from rest_framework import serializers
from core.models import BiometricIdentity


class BiometricIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometricIdentity
        fields = [
            "id", "user", "biometric_type", "biometric_hash",
            "encrypted_template", "is_active", "verified_at",
            "device_id", "fail_count", "created_at", "updated_at",
        ]
        read_only_fields = ["biometric_hash", "verified_at", "fail_count", "created_at", "updated_at"]


class BiometricRegisterSerializer(serializers.Serializer):
    biometric_type = serializers.ChoiceField(choices=BiometricIdentity.BiometricType.choices)
    encrypted_template = serializers.CharField()
    device_id = serializers.CharField(max_length=255, required=False, default="")


class BiometricVerifySerializer(serializers.Serializer):
    biometric_type = serializers.ChoiceField(choices=BiometricIdentity.BiometricType.choices)
    encrypted_template = serializers.CharField()
