from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import AIInsight, Patient
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.ai_clinical_service import AIClinicalService

from .serializers import (
    AIInsightSerializer, AIInsightReviewSerializer,
    RiskAssessmentSerializer, MedicationCheckSerializer,
)


class AIInsightListView(generics.ListAPIView):
    serializer_class = AIInsightSerializer
    filterset_fields = ["insight_type", "patient", "is_reviewed"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return AIInsight.objects.select_related("patient", "reviewed_by")


class AIInsightDetailView(generics.RetrieveAPIView):
    serializer_class = AIInsightSerializer

    def get_queryset(self):
        return AIInsight.objects.select_related("patient", "reviewed_by")


class AIInsightReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = AIInsightReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        insight = AIClinicalService.review_insight(
            pk, request.user,
            action_taken=serializer.validated_data.get("action_taken", ""),
        )
        if not insight:
            return Response({"success": False, "message": "Insight not found"}, status=404)

        result = AIInsightSerializer(insight)
        return Response({"success": True, "data": result.data})


class RiskAssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RiskAssessmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        try:
            insight = AIClinicalService.assess_risk(serializer.validated_data["patient_id"])
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient not found"}, status=404)

        result = AIInsightSerializer(insight)
        return Response({"success": True, "data": result.data})


class MedicationCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MedicationCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        try:
            insight = AIClinicalService.check_medication_interactions(serializer.validated_data["patient_id"])
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient not found"}, status=404)

        result = AIInsightSerializer(insight)
        return Response({"success": True, "data": result.data})


class DeteriorationDetectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        patient_id = request.data.get("patient_id")
        if not patient_id:
            return Response({"success": False, "message": "patient_id required"}, status=400)

        try:
            insight = AIClinicalService.detect_deterioration(patient_id)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient not found"}, status=404)

        result = AIInsightSerializer(insight)
        return Response({"success": True, "data": result.data})
