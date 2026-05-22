from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Patient, PatientHistory, AuditLog, User
from core.permissions import IsStaff, IsSuperAdmin, IsHospitalAdmin, IsDoctor, IsNurse
from .serializers import (
    PatientListSerializer,
    PatientDetailSerializer,
    PatientCreateSerializer,
    PatientUpdateSerializer,
    PatientHistorySerializer,
)
from .filters import PatientFilter


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.filter(is_active=True)
    filterset_class = PatientFilter
    search_fields = [
        "first_name",
        "last_name",
        "health_id",
        "national_id",
        "phone_number",
        "email",
    ]
    ordering_fields = [
        "first_name",
        "last_name",
        "created_at",
        "date_of_birth",
    ]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return PatientListSerializer
        if self.action == "retrieve":
            return PatientDetailSerializer
        if self.action == "create":
            return PatientCreateSerializer
        if self.action in ("update", "partial_update"):
            return PatientUpdateSerializer
        return PatientDetailSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsStaff()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsStaff()]
        if self.action == "list":
            return [IsAuthenticated(), IsStaff()]
        if self.action == "retrieve":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsStaff()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "data": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.READ,
            resource_type="patient",
            resource_id=instance.health_id,
            description=f"Viewed patient {instance.health_id}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path=f"/api/patients/{kwargs.get('pk')}/",
        )

        return Response({"success": True, "data": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.CREATE,
            resource_type="patient",
            resource_id=patient.health_id,
            description=f"Registered patient {patient.health_id} - {patient.full_name}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path="/api/patients/",
        )

        return Response(
            {
                "success": True,
                "message": "Patient registered successfully",
                "data": PatientDetailSerializer(patient).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            resource_type="patient",
            resource_id=patient.health_id,
            description=f"Updated patient {patient.health_id}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path=f"/api/patients/{kwargs.get('pk')}/",
        )

        return Response(
            {
                "success": True,
                "message": "Patient updated successfully",
                "data": PatientDetailSerializer(patient).data,
            }
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.DELETE,
            resource_type="patient",
            resource_id=instance.health_id,
            description=f"Deactivated patient {instance.health_id}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path=f"/api/patients/{kwargs.get('pk')}/",
        )

        return Response(
            {"success": True, "message": "Patient deactivated successfully"},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        patient = self.get_object()
        record_type = request.query_params.get("record_type")
        histories = PatientHistory.objects.filter(patient=patient)
        if record_type:
            histories = histories.filter(record_type=record_type)
        histories = histories.order_by("-recorded_at")
        page = self.paginate_queryset(histories)
        if page is not None:
            serializer = PatientHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PatientHistorySerializer(histories, many=True)
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=["post"])
    def add_history(self, request, pk=None):
        patient = self.get_object()
        serializer = PatientHistorySerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(patient=patient)

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.CREATE,
            resource_type="patient_history",
            resource_id=patient.health_id,
            description=f"Added medical record for patient {patient.health_id}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path=f"/api/patients/{pk}/add_history/",
        )

        return Response(
            {
                "success": True,
                "message": "Medical record added successfully",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def quick_search(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response(
                {
                    "success": True,
                    "data": [],
                    "message": "Search query must be at least 2 characters",
                }
            )

        from django.db.models import Q

        patients = self.get_queryset().filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(health_id__icontains=query)
            | Q(national_id__icontains=query)
            | Q(phone_number__icontains=query)
        )[:10]

        serializer = PatientListSerializer(patients, many=True)
        return Response({"success": True, "data": serializer.data})
