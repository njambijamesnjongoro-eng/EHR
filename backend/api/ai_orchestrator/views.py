from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import AIRecommendation, Patient
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.ai_orchestrator_service import AIOrchestratorService

from .serializers import (
    AIRecommendationSerializer, AIRecommendationActionSerializer,
    GenerateRecommendationSerializer, WorkflowOptimizationSerializer,
)


class AIRecommendationListView(generics.ListAPIView):
    serializer_class = AIRecommendationSerializer
    filterset_fields = ["recommendation_type", "priority", "patient", "is_accepted"]
    search_fields = ["title", "recommendation_text"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return AIRecommendation.objects.select_related("patient", "accepted_by")


class AIRecommendationDetailView(generics.RetrieveAPIView):
    serializer_class = AIRecommendationSerializer
    queryset = AIRecommendation.objects.select_related("patient", "accepted_by")


class AIRecommendationAcceptView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request, pk):
        try:
            rec = AIOrchestratorService.accept_recommendation(pk, request.user)
        except AIRecommendation.DoesNotExist:
            return Response({"success": False, "message": "Recommendation not found"}, status=404)
        result = AIRecommendationSerializer(rec)
        return Response({"success": True, "data": result.data})


class AIRecommendationRejectView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request, pk):
        serializer = AIRecommendationActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        try:
            rec = AIOrchestratorService.reject_recommendation(
                pk, request.user,
                reason=serializer.validated_data.get("rejection_reason", ""),
            )
        except AIRecommendation.DoesNotExist:
            return Response({"success": False, "message": "Recommendation not found"}, status=404)
        result = AIRecommendationSerializer(rec)
        return Response({"success": True, "data": result.data})


class GenerateClinicalRecommendationView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request):
        serializer = GenerateRecommendationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        try:
            rec = AIOrchestratorService.generate_clinical_recommendation(
                serializer.validated_data["patient_id"],
                serializer.validated_data.get("visit_id"),
            )
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient not found"}, status=404)
        result = AIRecommendationSerializer(rec)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class GeneratePreventiveRecommendationView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request):
        patient_id = request.data.get("patient_id")
        if not patient_id:
            return Response({"success": False, "message": "patient_id required"}, status=400)
        try:
            rec = AIOrchestratorService.generate_preventive_recommendation(patient_id)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient not found"}, status=404)
        result = AIRecommendationSerializer(rec)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class WorkflowOptimizationView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        data = AIOrchestratorService.analyze_workflow_optimization(hospital_id)
        return Response({"success": True, "data": data})
