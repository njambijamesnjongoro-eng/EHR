from datetime import timedelta

from django.db.models import Avg
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import SystemHealthMetric, SyncQueue, User, EventStreamLog
from core.permissions import IsHospitalAdmin, IsSuperAdmin

from .serializers import SystemHealthMetricSerializer, SystemHealthDashboardSerializer, EventStreamLogSerializer


class SystemHealthMetricListView(generics.ListAPIView):
    queryset = SystemHealthMetric.objects.select_related("hospital")
    serializer_class = SystemHealthMetricSerializer
    filterset_fields = ["metric_type", "hospital"]
    ordering = ["-recorded_at"]


class SystemHealthDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        since = timezone.now() - timedelta(hours=24)

        queue_depth = SyncQueue.objects.filter(status=SyncQueue.SyncStatus.PENDING).count()
        active_users = User.objects.filter(is_active=True).count()

        cache_hit = SystemHealthMetric.objects.filter(
            metric_type=SystemHealthMetric.MetricType.CACHE_HIT_RATIO,
            recorded_at__gte=since,
        ).aggregate(avg=Avg("value"))["avg"] or 0.0

        latency_avg = SystemHealthMetric.objects.filter(
            metric_type=SystemHealthMetric.MetricType.API_LATENCY,
            recorded_at__gte=since,
        ).aggregate(avg=Avg("value"))["avg"] or 0.0

        error_rate = SystemHealthMetric.objects.filter(
            metric_type=SystemHealthMetric.MetricType.ERROR_RATE,
            recorded_at__gte=since,
        ).aggregate(avg=Avg("value"))["avg"] or 0.0

        recent_metrics = SystemHealthMetric.objects.filter(
            recorded_at__gte=since,
        ).order_by("-recorded_at")[:50]

        return Response({
            "success": True,
            "data": {
                "queue_depth": queue_depth,
                "active_users": active_users,
                "cache_hit_ratio": round(cache_hit, 4),
                "recent_latency_avg": round(latency_avg, 2),
                "error_rate_24h": round(error_rate, 4),
                "recent_metrics": SystemHealthMetricSerializer(recent_metrics, many=True).data,
            },
        })


class PrometheusMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        from monitoring.metrics import prometheus_metrics
        return prometheus_metrics(request)


class HealthCheckAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        from monitoring.metrics import health_check
        return health_check(request)


class InfrastructureHealthView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        from services.infrastructure_service import InfrastructureOptimizationService
        data = InfrastructureOptimizationService.assess_system_health()
        return Response({"success": True, "data": data})


class OptimizationRecommendationsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        from services.infrastructure_service import InfrastructureOptimizationService
        data = InfrastructureOptimizationService.get_optimization_recommendations()
        return Response({"success": True, "data": data})


class SelfHealingView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        from services.infrastructure_service import InfrastructureOptimizationService
        data = InfrastructureOptimizationService.run_self_healing()
        return Response({"success": True, "data": data})


class EventStreamListView(generics.ListAPIView):
    queryset = EventStreamLog.objects.all()
    serializer_class = EventStreamLogSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filterset_fields = ["event_source", "event_type", "correlation_id"]
    ordering = ["-occurred_at"]


# ─── Phase 8 Extensions ───
from services.digital_twin_service import DigitalTwinService
from .serializers import InfrastructureTwinMonitorSerializer


class TwinMonitorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = InfrastructureTwinMonitorSerializer
    filterset_fields = ["twin_type", "simulation_status", "is_active"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return InfrastructureTwin.objects.select_related("hospital")


class TwinDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = InfrastructureTwinMonitorSerializer

    def get_queryset(self):
        return InfrastructureTwin.objects.select_related("hospital")
