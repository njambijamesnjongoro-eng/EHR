from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Hospital, Department, HospitalStaff
from core.permissions import IsSuperAdmin, IsHospitalAdmin, IsStaff
from .serializers import (
    HospitalSerializer, HospitalListSerializer,
    DepartmentSerializer, HospitalStaffSerializer,
)


class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    search_fields = ["hospital_name", "hospital_code", "county"]
    filterset_fields = ["hospital_type", "county", "is_active"]
    ordering_fields = ["hospital_name", "county", "created_at"]
    ordering = ["hospital_name"]

    def get_serializer_class(self):
        if self.action == "list":
            return HospitalListSerializer
        return HospitalSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role != "super_admin" and user.hospital_id:
            qs = qs.filter(id=user.hospital_id)
        return qs

    @action(detail=True, methods=["get"])
    def departments(self, request, pk=None):
        hospital = self.get_object()
        depts = hospital.departments.filter(is_active=True)
        serializer = DepartmentSerializer(depts, many=True)
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=["get"])
    def staff(self, request, pk=None):
        hospital = self.get_object()
        staff = hospital.staff_members.filter(is_active=True).select_related("user", "department")
        serializer = HospitalStaffSerializer(staff, many=True)
        return Response({"success": True, "data": serializer.data})


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.select_related("hospital").all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsHospitalAdmin]
    filterset_fields = ["hospital", "is_active"]
    search_fields = ["department_name"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role != "super_admin" and user.hospital_id:
            qs = qs.filter(hospital_id=user.hospital_id)
        return qs


class HospitalStaffViewSet(viewsets.ModelViewSet):
    queryset = HospitalStaff.objects.select_related("user", "hospital", "department").all()
    serializer_class = HospitalStaffSerializer
    permission_classes = [IsAuthenticated, IsHospitalAdmin]
    filterset_fields = ["hospital", "staff_role", "is_active", "department"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "employee_id"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role != "super_admin" and user.hospital_id:
            qs = qs.filter(hospital_id=user.hospital_id)
        return qs
