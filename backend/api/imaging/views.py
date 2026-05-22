from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.models import ImagingRequest, ImagingResult, AuditLog
from core.permissions import IsDoctor, IsStaff
from .serializers import (
    ImagingRequestListSerializer, ImagingRequestCreateSerializer,
    ImagingResultSerializer,
)


class ImagingRequestViewSet(viewsets.ModelViewSet):
    queryset = ImagingRequest.objects.select_related("patient", "requested_by").all()
    filterset_fields = ["status", "imaging_type", "priority", "patient"]
    search_fields = ["patient__first_name", "patient__last_name", "patient__health_id"]
    ordering = ["-requested_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return ImagingRequestCreateSerializer
        return ImagingRequestListSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsDoctor()]
        return [IsAuthenticated(), IsStaff()]

    def perform_create(self, serializer):
        img = serializer.save()
        AuditLog.objects.create(
            user=self.request.user, action=AuditLog.Action.CREATE,
            resource_type="imaging_request", resource_id=str(img.id),
            description=f"Imaging request: {img.get_imaging_type_display()} for {img.patient.health_id}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/imaging/requests/",
        )


class ImagingResultViewSet(viewsets.ModelViewSet):
    queryset = ImagingResult.objects.select_related(
        "imaging_request", "patient", "radiologist"
    ).all()
    serializer_class = ImagingResultSerializer
    permission_classes = [IsAuthenticated, IsStaff]
    ordering = ["-result_at"]

    def perform_create(self, serializer):
        result = serializer.save()
        AuditLog.objects.create(
            user=self.request.user, action=AuditLog.Action.CREATE,
            resource_type="imaging_result", resource_id=str(result.id),
            description=f"Imaging result uploaded for {result.patient.health_id}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/imaging/results/",
        )
