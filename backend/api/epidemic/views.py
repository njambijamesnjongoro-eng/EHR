from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import EpidemicAlert, PublicHealthForecast
from core.permissions import IsSuperAdmin
from services.epidemic_service import EpidemicIntelligenceService

from .serializers import EpidemicAlertSerializer, PublicHealthForecastSerializer


class EpidemicAlertListView(generics.ListAPIView):
    serializer_class = EpidemicAlertSerializer
    filterset_fields = ["alert_level", "alert_source", "disease_code", "county", "is_active"]
    ordering = ["-detected_at"]

    def get_queryset(self):
        return EpidemicAlert.objects.all()


class EpidemicAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EpidemicAlertSerializer
    queryset = EpidemicAlert.objects.all()


class DetectOutbreakView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        days = int(request.data.get("days", 7))
        alerts = EpidemicIntelligenceService.detect_outbreak_patterns(days)
        return Response({
            "success": True,
            "data": EpidemicAlertSerializer(alerts, many=True).data,
        })


class RegionalSpreadView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        disease_code = request.query_params.get("disease_code")
        days = int(request.query_params.get("days", 30))
        if not disease_code:
            return Response({"success": False, "message": "disease_code required"}, status=400)
        data = EpidemicIntelligenceService.regional_spread_model(disease_code, days)
        return Response({"success": True, "data": data})


class EpidemicForecastView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        disease_code = request.data.get("disease_code")
        county = request.data.get("county", "")
        days_ahead = int(request.data.get("days_ahead", 14))
        if not disease_code:
            return Response({"success": False, "message": "disease_code required"}, status=400)
        forecast = EpidemicIntelligenceService.generate_forecast(disease_code, county, days_ahead)
        result = PublicHealthForecastSerializer(forecast)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class ResolveAlertView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, pk):
        try:
            alert = EpidemicIntelligenceService.resolve_alert(pk)
        except EpidemicAlert.DoesNotExist:
            return Response({"success": False, "message": "Alert not found"}, status=404)
        result = EpidemicAlertSerializer(alert)
        return Response({"success": True, "data": result.data})
