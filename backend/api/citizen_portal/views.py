from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Patient
from services.citizen_service import CitizenPortalService
from services.citizen_super_portal_service import CitizenSuperPortalService
from services.wearable_service import WearableService
from services.telemedicine_service import TelemedicineExpansionService

from .serializers import CitizenHealthProfileSerializer, ProfileUpdateSerializer, HealthShareSerializer


class HealthSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)

        data = CitizenPortalService.get_health_summary(patient)
        return Response({"success": True, "data": data})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)

        profile = CitizenPortalService.get_or_create_profile(patient)
        result = CitizenHealthProfileSerializer(profile)
        return Response({"success": True, "data": result.data})

    def patch(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)

        serializer = ProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        profile = CitizenPortalService.update_profile(patient, serializer.validated_data)
        result = CitizenHealthProfileSerializer(profile)
        return Response({"success": True, "data": result.data})


class MyAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)

        telemed = TelemedicineExpansionService.get_patient_sessions(patient.id)
        return Response({
            "success": True,
            "data": [
                {
                    "id": t.id,
                    "doctor_name": f"{t.doctor.first_name} {t.doctor.last_name}" if t.doctor else "",
                    "scheduled_at": t.scheduled_at.isoformat(),
                    "status": t.status,
                    "session_type": t.session_type,
                    "meeting_url": t.meeting_url,
                }
                for t in telemed
            ],
        })


class MyPrescriptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)

        data = CitizenPortalService.get_prescription_history(patient)
        return Response({"success": True, "data": data})


class MyWearableDevicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)

        devices = WearableService.get_patient_devices(patient.id)
        from api.wearable.serializers import WearableDeviceSerializer
        return Response({
            "success": True,
            "data": WearableDeviceSerializer(devices, many=True).data,
        })


class MyReadingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)

        readings = WearableService.get_latest_readings(patient.id)
        return Response({"success": True, "data": readings})


class FullHealthRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)
        data = CitizenSuperPortalService.get_full_health_record(patient)
        return Response({"success": True, "data": data})


class EmergencyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)
        data = CitizenSuperPortalService.get_emergency_profile(patient)
        return Response({"success": True, "data": data})


class ShareHealthDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = HealthShareSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)
        result = CitizenSuperPortalService.share_health_data(
            patient,
            serializer.validated_data["recipient_email"],
            serializer.validated_data["data_types"],
            serializer.validated_data.get("expiry_hours", 24),
        )
        return Response({"success": True, "data": result})


class CareRemindersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)
        reminders = CitizenSuperPortalService.get_care_reminders(patient)
        return Response({"success": True, "data": reminders})


# ─── Phase 8 Extensions ───
from services.smart_automation_service import SmartAutomationService
from services.population_health_service import PopulationHealthService


class MyTelemetryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)
        data = SmartAutomationService.get_patient_telemetry(patient.id)
        return Response({"success": True, "data": data})


class MyPopulationInsightsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"success": False, "message": "Patient profile not found"}, status=404)
        county = request.query_params.get("county", "")
        data = PopulationHealthService.get_patient_population_context(patient, county)
        return Response({"success": True, "data": data})
