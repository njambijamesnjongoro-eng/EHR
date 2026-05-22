from rest_framework import serializers
from core.models import Patient, PatientHistory


class PatientListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "health_id",
            "first_name",
            "last_name",
            "full_name",
            "gender",
            "date_of_birth",
            "age",
            "phone_number",
            "email",
            "blood_group",
            "created_at",
        ]


class PatientDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "health_id",
            "first_name",
            "last_name",
            "full_name",
            "national_id",
            "date_of_birth",
            "age",
            "gender",
            "phone_number",
            "email",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "blood_group",
            "allergies",
            "chronic_conditions",
            "qr_code",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "health_id", "qr_code", "created_at", "updated_at"]


class PatientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "national_id",
            "date_of_birth",
            "gender",
            "phone_number",
            "email",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "blood_group",
            "allergies",
            "chronic_conditions",
        ]

    def validate_phone_number(self, value):
        import re
        if not re.match(r"^\+?1?\d{9,15}$", value):
            raise serializers.ValidationError(
                "Phone number must be 9-15 digits, optionally starting with + or 1"
            )
        return value

    def validate_national_id(self, value):
        if value and Patient.objects.filter(national_id=value).exists():
            raise serializers.ValidationError(
                "A patient with this National ID already exists"
            )
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        patient = Patient(**validated_data)
        if request and request.user.is_authenticated:
            patient.created_by = request.user
            patient.updated_by = request.user
        patient.save()
        return patient


class PatientUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "national_id",
            "date_of_birth",
            "gender",
            "phone_number",
            "email",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "blood_group",
            "allergies",
            "chronic_conditions",
        ]

    def validate_phone_number(self, value):
        import re
        if not re.match(r"^\+?1?\d{9,15}$", value):
            raise serializers.ValidationError(
                "Phone number must be 9-15 digits, optionally starting with + or 1"
            )
        return value

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            instance.updated_by = request.user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PatientHistorySerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientHistory
        fields = [
            "id",
            "patient",
            "record_type",
            "title",
            "description",
            "recorded_by",
            "recorded_by_name",
            "recorded_at",
            "is_confidential",
            "metadata",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "recorded_by",
            "recorded_at",
            "created_at",
        ]

    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.get_full_name()
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["recorded_by"] = request.user
        return super().create(validated_data)


class PatientSearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(
        choices=["male", "female", "other"], required=False
    )
    blood_group = serializers.ChoiceField(
        choices=[
            "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "unknown",
        ],
        required=False,
    )
    age_min = serializers.IntegerField(required=False, min_value=0)
    age_max = serializers.IntegerField(required=False, min_value=0)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
