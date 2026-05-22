from rest_framework import serializers
from core.models import Visit, VitalSign, Diagnosis, Prescription
from api.authentication.serializers import UserSerializer


# ─── Visit ───
class VisitListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Visit
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "visit_date",
            "chief_complaint",
            "status",
            "follow_up_date",
            "created_at",
        ]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_doctor_name(self, obj):
        if obj.doctor:
            return obj.doctor.get_full_name() or obj.doctor.email
        return None


class VisitDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    diagnoses = serializers.SerializerMethodField()
    prescriptions = serializers.SerializerMethodField()
    vital_signs = serializers.SerializerMethodField()

    class Meta:
        model = Visit
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "visit_date",
            "chief_complaint",
            "symptoms",
            "diagnosis_summary",
            "treatment_plan",
            "follow_up_date",
            "status",
            "notes",
            "diagnoses",
            "prescriptions",
            "vital_signs",
            "created_at",
            "updated_at",
        ]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_doctor_name(self, obj):
        if obj.doctor:
            return obj.doctor.get_full_name() or obj.doctor.email
        return None

    def get_diagnoses(self, obj):
        return DiagnosisSerializer(obj.diagnoses.all(), many=True).data

    def get_prescriptions(self, obj):
        return PrescriptionSerializer(obj.prescriptions.all(), many=True).data

    def get_vital_signs(self, obj):
        return VitalSignSerializer(obj.vital_signs.all(), many=True).data


class VisitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = [
            "patient",
            "chief_complaint",
            "symptoms",
            "diagnosis_summary",
            "treatment_plan",
            "follow_up_date",
            "notes",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None
        validated_data["doctor"] = user
        validated_data["created_by"] = user
        return super().create(validated_data)


class VisitUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = [
            "chief_complaint",
            "symptoms",
            "diagnosis_summary",
            "treatment_plan",
            "follow_up_date",
            "status",
            "notes",
        ]


# ─── Vital Signs ───
class VitalSignSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = VitalSign
        fields = [
            "id",
            "visit",
            "patient",
            "temperature",
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "pulse_rate",
            "respiratory_rate",
            "oxygen_saturation",
            "weight",
            "height",
            "bmi",
            "notes",
            "recorded_by",
            "recorded_by_name",
            "recorded_at",
        ]
        read_only_fields = ["id", "bmi", "recorded_by", "recorded_at"]

    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.get_full_name() or obj.recorded_by.email
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["recorded_by"] = request.user
        return super().create(validated_data)


# ─── Diagnosis ───
class DiagnosisSerializer(serializers.ModelSerializer):
    diagnosed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Diagnosis
        fields = [
            "id",
            "visit",
            "patient",
            "diagnosis_type",
            "diagnosis_name",
            "icd_code",
            "severity",
            "clinical_notes",
            "is_confirmed",
            "diagnosed_by",
            "diagnosed_by_name",
            "diagnosed_at",
            "created_at",
        ]
        read_only_fields = ["id", "diagnosed_by", "diagnosed_at", "created_at"]

    def get_diagnosed_by_name(self, obj):
        if obj.diagnosed_by:
            return obj.diagnosed_by.get_full_name() or obj.diagnosed_by.email
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["diagnosed_by"] = request.user
        return super().create(validated_data)


# ─── Prescription ───
class PrescriptionSerializer(serializers.ModelSerializer):
    prescribed_by_name = serializers.SerializerMethodField()
    dispensed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            "id",
            "visit",
            "patient",
            "medication_name",
            "dosage",
            "frequency",
            "duration_days",
            "duration_text",
            "route",
            "instructions",
            "prescribed_by",
            "prescribed_by_name",
            "prescribed_at",
            "is_dispensed",
            "dispensed_at",
            "dispensed_by",
            "dispensed_by_name",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id", "prescribed_by", "prescribed_at",
            "is_dispensed", "dispensed_at", "dispensed_by", "created_at",
        ]

    def get_prescribed_by_name(self, obj):
        if obj.prescribed_by:
            return obj.prescribed_by.get_full_name() or obj.prescribed_by.email
        return None

    def get_dispensed_by_name(self, obj):
        if obj.dispensed_by:
            return obj.dispensed_by.get_full_name() or obj.dispensed_by.email
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["prescribed_by"] = request.user
        return super().create(validated_data)


class PrescriptionDispenseSerializer(serializers.Serializer):
    prescription_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=1
    )
