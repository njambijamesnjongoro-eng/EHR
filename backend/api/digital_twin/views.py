from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import InfrastructureTwin
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.digital_twin_service import DigitalTwinService

from .serializers import (
    InfrastructureTwinSerializer, RunSimulationSerializer,
    CreateScenarioSerializer, CompareScenariosSerializer,
)


class InfrastructureTwinList(generics.ListAPIView):
    serializer_class = InfrastructureTwinSerializer
    filterset_fields = ["twin_type", "hospital", "region", "simulation_status", "is_active"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return InfrastructureTwin.objects.select_related("hospital")


class InfrastructureTwinDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InfrastructureTwinSerializer

    def get_queryset(self):
        return InfrastructureTwin.objects.select_related("hospital")


class RunSimulation(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request, pk):
        serializer = RunSimulationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        try:
            result = DigitalTwinService.run_simulation(
                pk, serializer.validated_data.get("parameters", {}),
            )
        except InfrastructureTwin.DoesNotExist:
            return Response({"success": False, "message": "Twin not found"}, status=404)
        return Response({"success": True, "data": result})


class TwinStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            twin = InfrastructureTwin.objects.get(pk=pk)
        except InfrastructureTwin.DoesNotExist:
            return Response({"success": False, "message": "Twin not found"}, status=404)
        data = {
            "id": twin.id,
            "name": twin.name,
            "simulation_status": twin.simulation_status,
            "last_simulated_at": twin.last_simulated_at,
            "is_active": twin.is_active,
        }
        return Response({"success": True, "data": data})


class CreateScenario(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request, pk):
        serializer = CreateScenarioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        try:
            scenario = DigitalTwinService.create_scenario(
                pk,
                name=serializer.validated_data["name"],
                parameters=serializer.validated_data["parameters"],
            )
        except InfrastructureTwin.DoesNotExist:
            return Response({"success": False, "message": "Twin not found"}, status=404)
        return Response({"success": True, "data": scenario}, status=status.HTTP_201_CREATED)


class CompareScenarios(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request):
        serializer = CompareScenariosSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        data = DigitalTwinService.compare_scenarios(
            serializer.validated_data["scenario_ids"],
        )
        return Response({"success": True, "data": data})
