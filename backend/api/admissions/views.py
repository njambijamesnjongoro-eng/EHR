from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.models import Ward, Bed, Admission, AuditLog, Notification
from core.permissions import IsStaff, IsHospitalAdmin
from .serializers import (
    WardSerializer, BedSerializer,
    AdmissionListSerializer, AdmissionCreateSerializer, AdmissionUpdateSerializer,
)


class WardViewSet(viewsets.ModelViewSet):
    queryset = Ward.objects.filter(is_active=True).prefetch_related("beds")
    serializer_class = WardSerializer
    permission_classes = [IsAuthenticated, IsStaff]

    @action(detail=True, methods=["get"])
    def beds(self, request, pk=None):
        ward = self.get_object()
        beds = ward.beds.all()
        serializer = BedSerializer(beds, many=True)
        return Response({"success": True, "data": serializer.data})


class BedViewSet(viewsets.ModelViewSet):
    queryset = Bed.objects.select_related("ward").all()
    serializer_class = BedSerializer
    permission_classes = [IsAuthenticated, IsStaff]
    filterset_fields = ["ward", "occupancy_status"]


class AdmissionViewSet(viewsets.ModelViewSet):
    queryset = Admission.objects.select_related(
        "patient", "ward", "bed", "admitted_by"
    ).all()
    filterset_fields = ["status", "ward", "patient"]
    search_fields = [
        "patient__first_name", "patient__last_name",
        "patient__health_id", "admission_reason",
    ]
    ordering_fields = ["admission_date", "status"]
    ordering = ["-admission_date"]

    def get_serializer_class(self):
        if self.action == "create":
            return AdmissionCreateSerializer
        if self.action in ("update", "partial_update", "discharge"):
            return AdmissionUpdateSerializer
        return AdmissionListSerializer

    def get_permissions(self):
        if self.action in ("create", "discharge"):
            return [IsAuthenticated(), IsHospitalAdmin()]
        return [IsAuthenticated(), IsStaff()]

    def perform_create(self, serializer):
        admission = serializer.save()
        AuditLog.objects.create(
            user=self.request.user, action=AuditLog.Action.CREATE,
            resource_type="admission", resource_id=str(admission.id),
            description=f"Admitted patient {admission.patient.health_id} to {admission.ward}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/admissions/admissions/",
        )

    @action(detail=True, methods=["post"])
    def discharge(self, request, pk=None):
        instance = self.get_object()
        if instance.status == Admission.Status.DISCHARGED:
            return Response(
                {"success": False, "message": "Patient already discharged"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = AdmissionUpdateSerializer(
            instance, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        AuditLog.objects.create(
            user=request.user, action=AuditLog.Action.UPDATE,
            resource_type="admission", resource_id=str(instance.id),
            description=f"Discharged patient {instance.patient.health_id}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path=f"/api/admissions/admissions/{pk}/discharge/",
        )

        return Response(
            {"success": True, "message": "Patient discharged successfully"},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def transfer(self, request, pk=None):
        instance = self.get_object()
        new_ward_id = request.data.get("ward")
        new_bed_id = request.data.get("bed")

        if not new_ward_id or not new_bed_id:
            return Response(
                {"success": False, "message": "Ward and bed are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_ward = instance.ward
        old_bed = instance.bed

        if old_bed:
            old_bed.occupancy_status = Bed.Status.AVAILABLE
            old_bed.save(update_fields=["occupancy_status"])

        try:
            new_bed = Bed.objects.get(id=new_bed_id)
            new_bed.occupancy_status = Bed.Status.OCCUPIED
            new_bed.save(update_fields=["occupancy_status"])
        except Bed.DoesNotExist:
            return Response(
                {"success": False, "message": "Bed not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        instance.ward_id = new_ward_id
        instance.bed = new_bed
        instance.save(update_fields=["ward", "bed"])

        AuditLog.objects.create(
            user=request.user, action=AuditLog.Action.UPDATE,
            resource_type="admission", resource_id=str(instance.id),
            description=f"Transferred patient from {old_ward} to {instance.ward}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path=f"/api/admissions/admissions/{pk}/transfer/",
        )

        return Response(
            {"success": True, "message": "Patient transferred successfully"},
            status=status.HTTP_200_OK,
        )
