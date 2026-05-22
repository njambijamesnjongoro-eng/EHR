from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import WearableDevice, DeviceReading
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.wearable_service import WearableService

from .serializers import (
    WearableDeviceSerializer, WearableRegisterSerializer,
    DeviceReadingSerializer, DeviceReadingIngestSerializer,
    DeviceReadingBulkSerializer, DeviceVerifySerializer,
)


class WearableDeviceListView(generics.ListAPIView):
    serializer_class = WearableDeviceSerializer
    filterset_fields = ["patient", "device_type", "is_active", "is_verified"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return WearableDevice.objects.select_related("patient").all()


class WearableDeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WearableDeviceSerializer

    def get_queryset(self):
        return WearableDevice.objects.select_related("patient")


class WearableRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WearableRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        patient_id = request.data.get("patient")
        if not patient_id:
            return Response({"success": False, "message": "patient is required"}, status=400)

        from core.models import Patient
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient not found"}, status=404)

        device = WearableService.register_device(
            patient=patient,
            device_type=serializer.validated_data["device_type"],
            device_name=serializer.validated_data["device_name"],
            manufacturer=serializer.validated_data.get("manufacturer", ""),
            model_number=serializer.validated_data.get("model_number", ""),
            serial_number=serializer.validated_data["serial_number"],
            firmware_version=serializer.validated_data.get("firmware_version", ""),
            config=serializer.validated_data.get("config", {}),
        )

        result = WearableDeviceSerializer(device)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class WearableVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = DeviceVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        success = WearableService.verify_device(pk, serializer.validated_data["pairing_token"])
        if success:
            return Response({"success": True, "message": "Device verified"})
        return Response({"success": False, "message": "Invalid pairing token"}, status=400)


class DeviceReadingIngestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceReadingIngestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        try:
            reading = WearableService.ingest_reading(
                device_id=serializer.validated_data["device_id"],
                patient_id=serializer.validated_data["patient_id"],
                reading_type=serializer.validated_data["reading_type"],
                value=serializer.validated_data["value"],
                unit=serializer.validated_data.get("unit", ""),
                recorded_at=serializer.validated_data.get("recorded_at"),
                metadata=serializer.validated_data.get("metadata"),
            )
        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=400)

        result = DeviceReadingSerializer(reading)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class DeviceReadingBulkIngestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceReadingBulkSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        results = WearableService.bulk_ingest(serializer.validated_data["readings"])
        return Response({
            "success": True,
            "data": {
                "ingested": len(results),
                "readings": DeviceReadingSerializer(results, many=True).data,
            },
        })


class DeviceReadingListView(generics.ListAPIView):
    serializer_class = DeviceReadingSerializer
    filterset_fields = ["patient", "device", "reading_type", "is_abnormal"]
    ordering = ["-recorded_at"]

    def get_queryset(self):
        return DeviceReading.objects.select_related("device", "patient").all()


class PatientLatestReadingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        readings = WearableService.get_latest_readings(patient_id)
        return Response({"success": True, "data": readings})
