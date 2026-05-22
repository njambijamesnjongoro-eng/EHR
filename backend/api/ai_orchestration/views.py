from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import AIModelRegistry
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.ai_orchestration_service import AIOrchestrationLayerService

from .serializers import AIModelRegistrySerializer, UpdateModelStatusSerializer


class ModelRegistryList(generics.ListAPIView):
    serializer_class = AIModelRegistrySerializer
    filterset_fields = ["model_type", "status", "is_active", "governance_approval"]
    search_fields = ["model_name", "description"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return AIModelRegistry.objects.select_related("approved_by")


class ModelRegistryDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AIModelRegistrySerializer

    def get_queryset(self):
        return AIModelRegistry.objects.select_related("approved_by")


class UpdateModelStatus(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, pk):
        serializer = UpdateModelStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        try:
            model = AIOrchestrationLayerService.update_model_status(
                pk,
                status=serializer.validated_data["status"],
                governance_approval=serializer.validated_data.get("governance_approval"),
                approved_by=request.user,
            )
        except AIModelRegistry.DoesNotExist:
            return Response({"success": False, "message": "Model not found"}, status=404)
        result = AIModelRegistrySerializer(model)
        return Response({"success": True, "data": result.data})


class ModelGovernanceReport(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        data = AIOrchestrationLayerService.get_governance_report()
        return Response({"success": True, "data": data})


class AIAuditTrail(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, pk):
        try:
            model = AIModelRegistry.objects.get(pk=pk)
        except AIModelRegistry.DoesNotExist:
            return Response({"success": False, "message": "Model not found"}, status=404)
        return Response({"success": True, "data": model.audit_trail})
