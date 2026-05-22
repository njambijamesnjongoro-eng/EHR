from rest_framework import serializers
from core.models import Hospital, Department, HospitalStaff


class HospitalSerializer(serializers.ModelSerializer):
    staff_count = serializers.SerializerMethodField()
    department_count = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]

    def get_staff_count(self, obj):
        return obj.staff_members.filter(is_active=True).count()

    def get_department_count(self, obj):
        return obj.departments.filter(is_active=True).count()


class HospitalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ["id", "hospital_name", "hospital_code", "hospital_type", "county", "is_active"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"
        read_only_fields = ["created_at"]


class HospitalStaffSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    hospital_name = serializers.CharField(source="hospital.hospital_name", read_only=True)
    department_name = serializers.CharField(source="department.department_name", read_only=True)

    class Meta:
        model = HospitalStaff
        fields = "__all__"
        read_only_fields = ["joined_at"]

    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def validate(self, data):
        if HospitalStaff.objects.filter(user=data["user"], hospital=data["hospital"]).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("User already belongs to this hospital")
        return data
