from rest_framework import serializers
from core.models import TelemedicineSession, TelemedicineInteraction


class TelemedicineSessionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_health_id = serializers.CharField(source="patient.health_id", read_only=True)
    doctor_name = serializers.SerializerMethodField()
    hospital_name = serializers.CharField(source="hospital.hospital_name", read_only=True)

    class Meta:
        model = TelemedicineSession
        fields = "__all__"
        read_only_fields = ["started_at", "ended_at", "status", "created_at", "updated_at"]

    def get_doctor_name(self, obj):
        return obj.doctor.get_full_name()


class TelemedicineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemedicineSession
        fields = ["patient", "doctor", "scheduled_at", "session_type", "consultation_notes"]
        read_only_fields = ["created_at", "updated_at"]


class TelemedicineActionSerializer(serializers.Serializer):
    consultation_notes = serializers.CharField(required=False, allow_blank=True)
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)


class TelemedicineInteractionSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    interaction_type_display = serializers.CharField(source="get_interaction_type_display", read_only=True)

    class Meta:
        model = TelemedicineInteraction
        fields = [
            "id", "session", "sender", "sender_name", "interaction_type",
            "interaction_type_display", "content", "file_url", "metadata",
            "is_encrypted", "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_sender_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}" if obj.sender else ""
