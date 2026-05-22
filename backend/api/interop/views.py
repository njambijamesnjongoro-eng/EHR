from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ExternalSystem
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.interop_service import InteroperabilityService

from .serializers import (
    ExternalSystemSerializer, ExternalSystemRegisterSerializer,
    FHIRConversionSerializer, IntegrationEventSerializer,
)
from services.compliance_service import ComplianceService


class ExternalSystemListView(generics.ListAPIView):
    queryset = ExternalSystem.objects.select_related("hospital")
    serializer_class = ExternalSystemSerializer
    filterset_fields = ["system_type", "is_active", "hospital"]
    ordering = ["-created_at"]


class ExternalSystemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExternalSystem.objects.select_related("hospital")
    serializer_class = ExternalSystemSerializer


class ExternalSystemRegisterView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request):
        serializer = ExternalSystemRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        system = InteroperabilityService.register_external_system(
            name=serializer.validated_data["system_name"],
            system_type=serializer.validated_data["system_type"],
            base_url=serializer.validated_data["base_url"],
            hospital=request.user.hospital,
            auth_type=serializer.validated_data.get("auth_type", "api_key"),
            config=serializer.validated_data.get("config", {}),
        )

        result = ExternalSystemSerializer(system)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class FHIRConversionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FHIRConversionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        resource_type = serializer.validated_data["resource_type"]
        data = serializer.validated_data["data"]

        fhir_resource = InteroperabilityService.convert_to_fhir(resource_type, data)
        return Response({"success": True, "data": fhir_resource})


class FHIRImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        fhir_resource = request.data
        internal = InteroperabilityService.convert_from_fhir(fhir_resource)
        return Response({"success": True, "data": internal})
