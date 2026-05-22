from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Referral, ReferralDocument, EnterpriseAuditEvent
from core.permissions import IsStaff, IsDoctor
from services.notification_service import NotificationService
from .serializers import (
    ReferralSerializer, ReferralCreateSerializer,
    ReferralActionSerializer, ReferralDocumentSerializer,
)


class ReferralViewSet(viewsets.ModelViewSet):
    queryset = Referral.objects.select_related(
        "patient", "referring_hospital", "receiving_hospital",
        "referring_doctor", "receiving_department"
    ).all()
    permission_classes = [IsAuthenticated, IsStaff]
    filterset_fields = ["status", "priority", "referring_hospital", "receiving_hospital", "patient"]
    search_fields = ["patient__first_name", "patient__last_name", "clinical_summary", "reason_for_referral"]
    ordering_fields = ["created_at", "priority"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return ReferralCreateSerializer
        return ReferralSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role != "super_admin" and user.hospital_id:
            qs = qs.filter(
                models.Q(referring_hospital_id=user.hospital_id) |
                models.Q(receiving_hospital_id=user.hospital_id)
            )
        return qs

    def perform_create(self, serializer):
        referral = serializer.save(
            referring_hospital_id=self.request.user.hospital_id,
            referring_doctor=self.request.user,
        )
        NotificationService.send_referral_notification(referral)

        EnterpriseAuditEvent.objects.create(
            event_type=EnterpriseAuditEvent.EventType.INTEGRATION,
            action="referral_created",
            resource_type="Referral",
            resource_id=str(referral.id),
            description=f"Referral created for {referral.patient.health_id} to {referral.receiving_hospital.hospital_code}",
        )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        referral = self.get_object()
        if referral.status != Referral.ReferralStatus.PENDING:
            return Response({"success": False, "message": "Referral is not pending"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReferralActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        referral.status = Referral.ReferralStatus.ACCEPTED
        referral.response_notes = serializer.validated_data.get("response_notes", "")
        referral.responded_by = request.user
        referral.responded_at = timezone.now()
        referral.save()

        return Response({"success": True, "message": "Referral accepted"})

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        referral = self.get_object()
        if referral.status != Referral.ReferralStatus.PENDING:
            return Response({"success": False, "message": "Referral is not pending"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReferralActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        referral.status = Referral.ReferralStatus.DECLINED
        referral.response_notes = serializer.validated_data.get("response_notes", "")
        referral.responded_by = request.user
        referral.responded_at = timezone.now()
        referral.save()

        return Response({"success": True, "message": "Referral declined"})

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        referral = self.get_object()
        referral.status = Referral.ReferralStatus.COMPLETED
        referral.completed_at = timezone.now()
        referral.save()
        return Response({"success": True, "message": "Referral completed"})


class ReferralDocumentViewSet(viewsets.ModelViewSet):
    queryset = ReferralDocument.objects.select_related("referral", "uploaded_by").all()
    serializer_class = ReferralDocumentSerializer
    permission_classes = [IsAuthenticated, IsStaff]



