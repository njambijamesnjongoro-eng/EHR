from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import SecurityEvent, DeviceFingerprint, MFAToken, InfrastructureEvent
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.security_service import SecurityService

from .serializers import (
    SecurityEventSerializer, SecurityEventResolveSerializer,
    DeviceFingerprintSerializer, MFATokenSerializer, MFATokenCodeSerializer,
    RiskDashboardSerializer, InfrastructureEventMonitorSerializer,
)


class SecurityEventListView(generics.ListAPIView):
    queryset = SecurityEvent.objects.select_related("user", "hospital")
    serializer_class = SecurityEventSerializer
    filterset_fields = ["category", "severity", "resolved", "user"]
    search_fields = ["description", "ip_address"]
    ordering_fields = ["detected_at", "risk_score", "severity"]
    ordering = ["-detected_at"]


class SecurityEventDetailView(generics.RetrieveUpdateAPIView):
    queryset = SecurityEvent.objects.select_related("user", "hospital")
    serializer_class = SecurityEventSerializer


class SecurityEventResolveView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request, pk):
        try:
            event = SecurityEvent.objects.get(pk=pk)
        except SecurityEvent.DoesNotExist:
            return Response({"success": False, "message": "Event not found"}, status=404)

        event.resolved = True
        event.resolved_by = request.user
        event.resolved_at = timezone.now()
        event.save(update_fields=["resolved", "resolved_by", "resolved_at"])

        serializer = SecurityEventSerializer(event)
        return Response({"success": True, "data": serializer.data})


class DeviceFingerprintListView(generics.ListAPIView):
    queryset = DeviceFingerprint.objects.select_related("user")
    serializer_class = DeviceFingerprintSerializer
    filterset_fields = ["is_trusted", "user"]
    ordering = ["-last_seen_at"]


class DeviceFingerprintDetailView(generics.RetrieveUpdateAPIView):
    queryset = DeviceFingerprint.objects.select_related("user")
    serializer_class = DeviceFingerprintSerializer


class DeviceTrustView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request, pk):
        try:
            device = DeviceFingerprint.objects.get(pk=pk)
        except DeviceFingerprint.DoesNotExist:
            return Response({"success": False, "message": "Device not found"}, status=404)

        device.is_trusted = True
        device.risk_count = 0
        device.save(update_fields=["is_trusted", "risk_count"])

        serializer = DeviceFingerprintSerializer(device)
        return Response({"success": True, "data": serializer.data})


class MFASetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token_type = request.data.get("token_type", MFAToken.TokenType.TOTP)
        token = SecurityService.setup_mfa(request.user, token_type)
        return Response({
            "success": True,
            "data": {
                "secret": token.secret,
                "token_type": token.token_type,
                "backup_codes": [],
            },
        }, status=status.HTTP_201_CREATED)


class MFAVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MFATokenCodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        valid = SecurityService.verify_mfa(request.user, serializer.validated_data["token_code"])
        if valid:
            MFAToken.objects.filter(user=request.user, token_type=MFAToken.TokenType.TOTP).update(verified_at=timezone.now())
            return Response({"success": True, "message": "MFA verified"})

        SecurityService.log_security_event(
            SecurityEvent.EventCategory.AUTH_FAILURE,
            SecurityEvent.Severity.MEDIUM,
            "Failed MFA verification",
            user=request.user, request=request,
        )
        return Response({"success": False, "message": "Invalid token"}, status=401)


class MFADisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        MFAToken.objects.filter(user=request.user).update(is_active=False)
        return Response({"success": True, "message": "MFA disabled"})


class RiskDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        since = timezone.now() - timedelta(hours=24)

        total_high_risk = SecurityEvent.objects.filter(
            detected_at__gte=since, risk_score__gte=0.7,
        ).count()

        critical_events = SecurityEvent.objects.filter(
            detected_at__gte=since, severity__in=["high", "critical"],
        ).count()

        unique_flagged = SecurityEvent.objects.filter(
            detected_at__gte=since, risk_score__gte=0.5,
        ).values("user").distinct().count()

        unresolved = SecurityEvent.objects.filter(
            resolved=False, severity__in=["high", "critical"],
        ).select_related("user")[:20]

        return Response({
            "success": True,
            "data": {
                "total_high_risk": total_high_risk,
                "critical_events_24h": critical_events,
                "unique_users_flagged": unique_flagged,
                "recent_unresolved": SecurityEventSerializer(unresolved, many=True).data,
            },
        })


class BehavioralAnomalyView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, user_id):
        from services.advanced_security_service import AdvancedSecurityService
        from core.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"success": False, "message": "User not found"}, status=404)

        data = AdvancedSecurityService.analyze_behavioral_anomaly(user)
        return Response({"success": True, "data": data})


class ThreatHuntingView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        from services.advanced_security_service import AdvancedSecurityService
        days = int(request.query_params.get("days", 7))
        data = AdvancedSecurityService.threat_hunting(days)
        return Response({"success": True, "data": data})


class PrivilegeAbuseView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        from services.advanced_security_service import AdvancedSecurityService
        days = int(request.query_params.get("days", 7))
        data = AdvancedSecurityService.detect_privilege_abuse(days)
        return Response({"success": True, "data": data})


class CorrelatedEventsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        correlation_id = request.query_params.get("correlation_id")
        if not correlation_id:
            return Response({"success": False, "message": "correlation_id required"}, status=400)

        from services.advanced_security_service import AdvancedSecurityService
        data = AdvancedSecurityService.correlated_event_analysis(correlation_id)
        return Response({"success": True, "data": data})


class DistributedAuditView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        from services.advanced_security_service import AdvancedSecurityService
        days = int(request.query_params.get("days", 30))
        data = AdvancedSecurityService.distributed_audit_analysis(days)
        return Response({"success": True, "data": data})


class InfrastructureEventMonitorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = InfrastructureEventMonitorSerializer
    filterset_fields = ["event_type", "severity", "service_name", "resolved"]
    ordering = ["-occurred_at"]

    def get_queryset(self):
        return InfrastructureEvent.objects.all()


# ─── Phase 8 Extensions ───
from services.threat_intelligence_service import ThreatIntelligenceService
from .serializers import OperationalAlertSerializer


class OperationalAlertListView(generics.ListAPIView):
    serializer_class = OperationalAlertSerializer
    filterset_fields = ["category", "severity", "hospital", "is_resolved", "is_acknowledged"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return OperationalAlert.objects.select_related("hospital", "acknowledged_by")


class ThreatIntelReportView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 7))
        data = ThreatIntelligenceService.generate_threat_report(days)
        return Response({"success": True, "data": data})


class LoginAnomalyView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 7))
        data = ThreatIntelligenceService.detect_login_anomalies(days)
        return Response({"success": True, "data": data})


class PrivilegeEscalationView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 7))
        data = ThreatIntelligenceService.detect_privilege_escalation(days)
        return Response({"success": True, "data": data})
