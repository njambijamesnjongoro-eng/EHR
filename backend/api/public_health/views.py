from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import PublicHealthMetric
from core.permissions import IsSuperAdmin
from services.public_health_analytics import PublicHealthAnalyticsService
from services.epidemic_service import EpidemicIntelligenceService

from .serializers import PublicHealthMetricSerializer, PublicHealthForecastSerializer


class PublicHealthMetricListView(generics.ListAPIView):
    queryset = PublicHealthMetric.objects.all()
    serializer_class = PublicHealthMetricSerializer
    filterset_fields = ["metric_category", "county", "disease_code"]
    ordering = ["-period_end"]


class DiseasePrevalenceView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 90))
        data = PublicHealthAnalyticsService.disease_prevalence(days)
        return Response({"success": True, "data": data})


class OutbreakSignalView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 14))
        signals = PublicHealthAnalyticsService.outbreak_signals(days)
        return Response({"success": True, "data": signals})


class CountyHeatmapView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        disease_code = request.query_params.get("disease_code", "")
        days = int(request.query_params.get("days", 30))
        data = PublicHealthAnalyticsService.county_disease_heatmap(disease_code or None, days)
        return Response({"success": True, "data": data})


class HealthcareBurdenView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        data = PublicHealthAnalyticsService.healthcare_burden(days)
        return Response({"success": True, "data": data})


class VaccinationAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        data = PublicHealthAnalyticsService.vaccination_analytics()
        return Response({"success": True, "data": data})


class MortalityTrendsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 365))
        data = PublicHealthAnalyticsService.mortality_trends(days)
        return Response({"success": True, "data": data})


class DiseaseForecastView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        disease_code = request.query_params.get("disease_code")
        county = request.query_params.get("county", "")
        days_ahead = int(request.query_params.get("days_ahead", 14))
        if not disease_code:
            return Response({"success": False, "message": "disease_code required"}, status=400)
        forecast = EpidemicIntelligenceService.generate_forecast(disease_code, county, days_ahead)
        result = PublicHealthForecastSerializer(forecast)
        return Response({"success": True, "data": result.data})
