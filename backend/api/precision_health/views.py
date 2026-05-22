from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import HealthRiskProfile, Patient
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.precision_health_service import PrecisionHealthService

from .serializers import (
    HealthRiskProfileSerializer, RiskAssessmentSerializer, HighRiskQuerySerializer,
)


class HealthRiskProfileListView(generics.ListAPIView):
    serializer_class = HealthRiskProfileSerializer
    filterset_fields = ["risk_category", "risk_level", "patient", "is_active"]
    ordering = ["-risk_score"]

    def get_queryset(self):
        return HealthRiskProfile.objects.select_related("patient")


class HealthRiskProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = HealthRiskProfileSerializer
    queryset = HealthRiskProfile.objects.select_related("patient")


class AssessRiskView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request):
        serializer = RiskAssessmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        try:
            profile = PrecisionHealthService.assess_risk(
                serializer.validated_data["patient_id"],
                serializer.validated_data["risk_category"],
            )
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient not found"}, status=404)
        result = HealthRiskProfileSerializer(profile)
        return Response({"success": True, "data": result.data})


class PatientRiskSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request, patient_id):
        data = PrecisionHealthService.get_patient_risk_summary(patient_id)
        return Response({"success": True, "data": data})


class HighRiskPatientsView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        category = request.query_params.get("category")
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        limit = int(request.query_params.get("limit", 50))
        profiles = PrecisionHealthService.get_high_risk_patients(category, hospital_id, limit)
        return Response({
            "success": True,
            "data": HealthRiskProfileSerializer(profiles, many=True).data,
        })


class RiskTrendsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        category = request.query_params.get("category")
        days = int(request.query_params.get("days", 90))
        if not category:
            return Response({"success": False, "message": "category required"}, status=400)
        data = PrecisionHealthService.get_risk_trends(category, days)
        return Response({"success": True, "data": data})
