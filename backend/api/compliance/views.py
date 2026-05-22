from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ConsentLog, EnterpriseAuditEvent, Patient
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.compliance_service import ComplianceService

from .serializers import (
    ConsentLogSerializer, ConsentGrantSerializer, ConsentRevokeSerializer,
    EnterpriseAuditEventSerializer, AuditReportSerializer,
)


class ConsentLogListView(generics.ListCreateAPIView):
    queryset = ConsentLog.objects.select_related("patient", "granted_by")
    serializer_class = ConsentLogSerializer
    filterset_fields = ["consent_type", "status", "patient"]
    ordering = ["-granted_at"]

    def perform_create(self, serializer):
        serializer.save(granted_by=self.request.user)


class ConsentLogDetailView(generics.RetrieveAPIView):
    queryset = ConsentLog.objects.select_related("patient", "granted_by")
    serializer_class = ConsentLogSerializer


class ConsentGrantView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConsentGrantSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        patient_id = request.data.get("patient")
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient not found"}, status=404)

        consent = ComplianceService.record_consent(
            patient=patient,
            consent_type=serializer.validated_data["consent_type"],
            granted_by=request.user,
            consent_version=serializer.validated_data.get("consent_version", "1.0"),
            metadata=serializer.validated_data.get("metadata", {}),
            expires_days=serializer.validated_data.get("expires_days"),
        )

        result = ConsentLogSerializer(consent)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class ConsentRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            consent = ConsentLog.objects.get(pk=pk)
        except ConsentLog.DoesNotExist:
            return Response({"success": False, "message": "Consent not found"}, status=404)

        serializer = ConsentRevokeSerializer(data=request.data)
        reason = serializer.validated_data.get("reason", "") if serializer.is_valid() else ""

        ComplianceService.revoke_consent(consent, revoked_by=request.user, reason=reason)

        result = ConsentLogSerializer(consent)
        return Response({"success": True, "data": result.data})


class AuditEventListView(generics.ListAPIView):
    queryset = EnterpriseAuditEvent.objects.select_related("user", "hospital")
    serializer_class = EnterpriseAuditEventSerializer
    filterset_fields = ["event_type", "severity", "action", "user"]
    search_fields = ["description", "resource_type", "resource_id"]
    ordering = ["-created_at"]


class AuditReportView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        report = ComplianceService.generate_audit_report(days)
        return Response({"success": True, "data": report})
