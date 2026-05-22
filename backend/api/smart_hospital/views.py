from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import SmartHospitalDevice, Ward, Hospital, SmartDeviceEvent
from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.smart_hospital_service import SmartHospitalService
from services.advanced_iot_service import AdvancedIoTService
from services.smart_hospital_automation import SmartHospitalAutomationService

from .serializers import (
    SmartHospitalDeviceSerializer, SmartHospitalRegisterSerializer,
    HeartbeatSerializer, SmartDeviceEventSerializer, DeviceIngestSerializer,
)


class SmartHospitalDeviceListView(generics.ListAPIView):
    serializer_class = SmartHospitalDeviceSerializer
    filterset_fields = ["hospital", "ward", "device_category", "is_online", "is_active"]
    ordering = ["device_category", "device_name"]

    def get_queryset(self):
        return SmartHospitalDevice.objects.select_related("hospital", "ward", "bed").all()


class SmartHospitalDeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SmartHospitalDeviceSerializer

    def get_queryset(self):
        return SmartHospitalDevice.objects.select_related("hospital", "ward", "bed")


class SmartHospitalRegisterView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request):
        serializer = SmartHospitalRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        hospital_id = request.data.get("hospital") or request.user.hospital_id
        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            return Response({"success": False, "message": "Hospital not found"}, status=404)

        ward = None
        if serializer.validated_data.get("ward_id"):
            try:
                ward = Ward.objects.get(id=serializer.validated_data["ward_id"])
            except Ward.DoesNotExist:
                pass

        device = SmartHospitalService.register_device(
            hospital=hospital,
            device_category=serializer.validated_data["device_category"],
            device_name=serializer.validated_data["device_name"],
            serial_number=serializer.validated_data["serial_number"],
            ward=ward,
            ip_address=serializer.validated_data.get("ip_address"),
            mac_address=serializer.validated_data.get("mac_address", ""),
            firmware_version=serializer.validated_data.get("firmware_version", ""),
            config=serializer.validated_data.get("config", {}),
        )

        result = SmartHospitalDeviceSerializer(device)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class HeartbeatView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = HeartbeatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        success = SmartHospitalService.record_heartbeat(serializer.validated_data["device_id"])
        if success:
            return Response({"success": True, "message": "Heartbeat recorded"})
        return Response({"success": False, "message": "Device not found"}, status=404)


class BedOccupancyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, hospital_id):
        data = SmartHospitalService.get_bed_occupancy_summary(hospital_id)
        return Response({"success": True, "data": data})


class OfflineDevicesView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        minutes = int(request.query_params.get("minutes", 15))
        devices = SmartHospitalService.detect_offline_devices(hospital_id, minutes)

        return Response({
            "success": True,
            "data": {
                "offline_count": len(devices),
                "devices": SmartHospitalDeviceSerializer(devices, many=True).data,
            },
        })


class SmartDeviceEventListView(generics.ListAPIView):
    serializer_class = SmartDeviceEventSerializer
    filterset_fields = ["hospital", "ward", "event_category", "severity", "is_processed"]
    ordering = ["-occurred_at"]

    def get_queryset(self):
        return SmartDeviceEvent.objects.select_related("device", "ward")


class SmartDeviceEventDetailView(generics.RetrieveAPIView):
    serializer_class = SmartDeviceEventSerializer
    queryset = SmartDeviceEvent.objects.select_related("device", "ward")


class IngestDeviceEventView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request):
        serializer = DeviceIngestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        try:
            event = AdvancedIoTService.ingest_smart_event(
                device_id=serializer.validated_data["device_id"],
                event_category=serializer.validated_data["event_category"],
                event_type=serializer.validated_data["event_type"],
                value=serializer.validated_data.get("value"),
                payload=serializer.validated_data.get("payload", {}),
                severity=serializer.validated_data.get("severity", "info"),
            )
        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=404)
        result = SmartDeviceEventSerializer(event)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class DeviceHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, device_id):
        data = AdvancedIoTService.get_device_health(device_id)
        return Response({"success": True, "data": data})


class HospitalIoTSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        data = AdvancedIoTService.get_hospital_iot_summary(hospital_id)
        return Response({"success": True, "data": data})


class PatientFlowAnalysisView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        days = int(request.query_params.get("days", 7))
        data = SmartHospitalAutomationService.analyze_patient_flow(hospital_id, days)
        return Response({"success": True, "data": data})


class BottleneckDetectionView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        data = SmartHospitalAutomationService.detect_bottlenecks(hospital_id)
        return Response({"success": True, "data": data})


class PredictiveStaffingView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        days = int(request.query_params.get("days_ahead", 7))
        data = SmartHospitalAutomationService.predictive_staffing(hospital_id, days)
        return Response({"success": True, "data": data})


class EquipmentUtilizationView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        data = SmartHospitalAutomationService.equipment_utilization(hospital_id)
        return Response({"success": True, "data": data})


# ─── Phase 8 Extensions ───
from core.models import SmartHospitalMetric, DeviceTelemetryEvent
from services.smart_automation_service import SmartAutomationService
from .serializers import SmartHospitalMetricSerializer


class SmartMetricListView(generics.ListAPIView):
    serializer_class = SmartHospitalMetricSerializer
    filterset_fields = ["hospital", "ward", "metric_category", "is_alert"]
    ordering = ["-recorded_at"]

    def get_queryset(self):
        return SmartHospitalMetric.objects.select_related("hospital", "ward")


class HospitalTelemetrySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        data = SmartAutomationService.get_telemetry_summary(hospital_id)
        return Response({"success": True, "data": data})


class RecordDeviceTelemetryView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def post(self, request):
        device_id = request.data.get("device_id")
        telemetry_type = request.data.get("telemetry_type")
        metric_name = request.data.get("metric_name")
        metric_value = request.data.get("metric_value")
        if not all([device_id, telemetry_type, metric_name, metric_value is not None]):
            return Response({"success": False, "message": "device_id, telemetry_type, metric_name, metric_value required"}, status=400)
        event = SmartAutomationService.record_device_telemetry(
            device_id=device_id,
            telemetry_type=telemetry_type,
            metric_name=metric_name,
            metric_value=metric_value,
            unit=request.data.get("unit", ""),
            hospital_id=request.data.get("hospital_id"),
            payload=request.data.get("payload", {}),
        )
        return Response({"success": True, "data": {"id": event.id, "recorded_at": event.recorded_at}}, status=status.HTTP_201_CREATED)
