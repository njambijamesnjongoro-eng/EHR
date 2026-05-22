from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import PopulationHealthInsight, PredictiveForecast
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.population_health_service import PopulationHealthService
from services.operational_intelligence_service import OperationalIntelligenceService

from .serializers import (
    PopulationHealthInsightSerializer, PredictiveForecastSerializer,
    RecordInsightSerializer, RecordForecastSerializer,
)


class PopulationInsightList(generics.ListAPIView):
    serializer_class = PopulationHealthInsightSerializer
    filterset_fields = ["category", "county", "region", "is_anonymized"]
    ordering = ["-period_end"]

    def get_queryset(self):
        return PopulationHealthInsight.objects.all()


class RecordInsight(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = RecordInsightSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        insight = PopulationHealthService.record_insight(serializer.validated_data)
        result = PopulationHealthInsightSerializer(insight)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class DiseaseBurden(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        county = request.query_params.get("county")
        data = PopulationHealthService.get_disease_burden(county)
        return Response({"success": True, "data": data})


class HealthcareAccess(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        county = request.query_params.get("county")
        data = PopulationHealthService.get_healthcare_access(county)
        return Response({"success": True, "data": data})


class HealthEquity(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        county = request.query_params.get("county")
        data = PopulationHealthService.get_health_equity(county)
        return Response({"success": True, "data": data})


class RegionalComparison(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get("category")
        if not category:
            return Response({"success": False, "message": "category required"}, status=400)
        data = PopulationHealthService.get_regional_comparison(category)
        return Response({"success": True, "data": data})


class PredictiveForecastList(generics.ListAPIView):
    serializer_class = PredictiveForecastSerializer
    filterset_fields = ["domain", "hospital", "county", "region"]
    ordering = ["-forecast_date"]

    def get_queryset(self):
        return PredictiveForecast.objects.select_related("hospital")


class RecordForecast(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = RecordForecastSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        forecast = OperationalIntelligenceService.record_forecast(serializer.validated_data)
        result = PredictiveForecastSerializer(forecast)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)
