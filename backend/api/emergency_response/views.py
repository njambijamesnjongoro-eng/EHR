from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import EmergencyResponseEvent
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.emergency_response_service import EmergencyResponseService

from .serializers import EmergencyResponseEventSerializer, UpdateStatusSerializer


class EmergencyEventList(generics.ListAPIView):
    serializer_class = EmergencyResponseEventSerializer
    filterset_fields = ["emergency_type", "severity", "status", "location_region"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return EmergencyResponseEvent.objects.select_related("incident_commander")


class EmergencyEventDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyResponseEventSerializer

    def get_queryset(self):
        return EmergencyResponseEvent.objects.select_related("incident_commander")


class UpdateStatus(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request, pk):
        serializer = UpdateStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        try:
            event = EmergencyResponseService.update_status(
                pk, serializer.validated_data["status"],
            )
        except EmergencyResponseEvent.DoesNotExist:
            return Response({"success": False, "message": "Event not found"}, status=404)
        result = EmergencyResponseEventSerializer(event)
        return Response({"success": True, "data": result.data})


class ActiveEmergencies(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = EmergencyResponseService.get_active_emergencies()
        return Response({"success": True, "data": data})


class RegionalCapacity(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        region = request.query_params.get("region")
        if not region:
            return Response({"success": False, "message": "region required"}, status=400)
        data = EmergencyResponseService.get_regional_capacity(region)
        return Response({"success": True, "data": data})


class NationalOverview(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        data = EmergencyResponseService.get_national_overview()
        return Response({"success": True, "data": data})
