from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.models import LabRequest, LabResult, AuditLog
from core.permissions import IsDoctor, IsStaff
from .serializers import (
    LabRequestListSerializer,
    LabRequestCreateSerializer,
    LabRequestUpdateSerializer,
    LabResultSerializer,
)


class LabRequestViewSet(viewsets.ModelViewSet):
    queryset = LabRequest.objects.select_related("patient", "requested_by").all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "priority", "patient"]
    search_fields = ["test_name", "patient__first_name", "patient__last_name", "patient__health_id"]
    ordering_fields = ["requested_at", "priority", "status"]
    ordering = ["-requested_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return LabRequestListSerializer
        if self.action == "create":
            return LabRequestCreateSerializer
        if self.action in ("update", "partial_update"):
            return LabRequestUpdateSerializer
        return LabRequestListSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsDoctor()]
        if self.action in ("update", "partial_update"):
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated(), IsStaff()]

    def perform_create(self, serializer):
        lab = serializer.save()

        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            resource_type="lab_request",
            resource_id=str(lab.id),
            description=f"Lab request: {lab.test_name} for patient {lab.patient.health_id}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/labs/requests/",
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        lab = self.get_object()
        lab.status = LabRequest.Status.CANCELLED
        lab.save(update_fields=["status"])

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            resource_type="lab_request",
            resource_id=str(lab.id),
            description=f"Cancelled lab request {lab.test_name}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path=f"/api/labs/requests/{pk}/cancel/",
        )

        return Response(
            {"success": True, "message": "Lab request cancelled"},
            status=status.HTTP_200_OK,
        )


class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.select_related("lab_request", "patient", "performed_by").all()
    serializer_class = LabResultSerializer
    ordering = ["-result_at"]

    def get_permissions(self):
        return [IsAuthenticated(), IsStaff()]

    def perform_create(self, serializer):
        result = serializer.save()

        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            resource_type="lab_result",
            resource_id=str(result.id),
            description=f"Lab result uploaded for {result.lab_request.test_name} - patient {result.patient.health_id}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/labs/results/",
        )
