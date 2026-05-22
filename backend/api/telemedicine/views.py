from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import TelemedicineSession, TelemedicineRecording, TelemedicineInteraction
from core.permissions import IsDoctor, IsStaff, IsHospitalAdmin
from services.telemedicine_service import TelemedicineExpansionService
from .serializers import (
    TelemedicineSessionSerializer, TelemedicineCreateSerializer,
    TelemedicineActionSerializer, TelemedicineInteractionSerializer,
)


class TelemedicineSessionViewSet(viewsets.ModelViewSet):
    queryset = TelemedicineSession.objects.select_related(
        "patient", "doctor", "hospital"
    ).all()
    permission_classes = [IsAuthenticated, IsStaff]
    filterset_fields = ["status", "session_type", "doctor", "patient", "hospital"]
    ordering_fields = ["scheduled_at"]
    ordering = ["-scheduled_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return TelemedicineCreateSerializer
        return TelemedicineSessionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "patient":
            qs = qs.filter(patient__created_by=user)
        elif user.role != "super_admin" and user.hospital_id:
            qs = qs.filter(hospital_id=user.hospital_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(hospital_id=self.request.user.hospital_id)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        session = self.get_object()
        if session.status != TelemedicineSession.SessionStatus.SCHEDULED:
            return Response({"success": False, "message": "Session is not scheduled"}, status=status.HTTP_400_BAD_REQUEST)

        session.status = TelemedicineSession.SessionStatus.IN_PROGRESS
        session.started_at = timezone.now()
        session.save(update_fields=["status", "started_at"])
        return Response({"success": True, "message": "Session started"})

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        session = self.get_object()
        serializer = TelemedicineActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session.status = TelemedicineSession.SessionStatus.COMPLETED
        session.ended_at = timezone.now()
        if serializer.validated_data.get("consultation_notes"):
            session.consultation_notes = serializer.validated_data["consultation_notes"]
        session.save()
        return Response({"success": True, "message": "Session completed"})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        session = self.get_object()
        serializer = TelemedicineActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session.status = TelemedicineSession.SessionStatus.CANCELLED
        session.cancellation_reason = serializer.validated_data.get("cancellation_reason", "")
        session.save()
        return Response({"success": True, "message": "Session cancelled"})

    @action(detail=True, methods=["get"])
    def recordings(self, request, pk=None):
        session = self.get_object()
        recordings = TelemedicineRecording.objects.filter(session=session).order_by("-created_at")
        return Response({
            "success": True,
            "data": [
                {
                    "id": r.id,
                    "recording_type": r.recording_type,
                    "file_url": r.file_url,
                    "duration_seconds": r.duration_seconds,
                    "created_at": r.created_at.isoformat(),
                }
                for r in recordings
            ],
        })

    @action(detail=True, methods=["post"])
    def add_recording(self, request, pk=None):
        session = self.get_object()
        recording = TelemedicineExpansionService.add_recording(
            session_id=session.id,
            recording_type=request.data.get("recording_type", "notes"),
            file_url=request.data.get("file_url", ""),
            duration_seconds=int(request.data.get("duration_seconds", 0)),
        )
        return Response({
            "success": True,
            "data": {
                "id": recording.id,
                "recording_type": recording.recording_type,
                "file_url": recording.file_url,
                "duration_seconds": recording.duration_seconds,
            },
        }, status=status.HTTP_201_CREATED)


class TelemedicineStatisticsView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.user.hospital_id
        days = int(request.query_params.get("days", 30))
        data = TelemedicineExpansionService.get_session_statistics(hospital_id, days)
        return Response({"success": True, "data": data})


class DoctorScheduleView(generics.ListAPIView):
    serializer_class = TelemedicineSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        doctor_id = self.request.query_params.get("doctor_id") or self.request.user.id
        from django.utils import timezone
        return TelemedicineSession.objects.filter(
            doctor_id=doctor_id,
            scheduled_at__gte=timezone.now(),
        ).select_related("patient", "doctor", "hospital").order_by("scheduled_at")


class TelemedicineInteractionListView(generics.ListAPIView):
    serializer_class = TelemedicineInteractionSerializer
    filterset_fields = ["session", "sender", "interaction_type"]
    ordering = ["created_at"]

    def get_queryset(self):
        return TelemedicineInteraction.objects.select_related("sender")


class TelemedicineInteractionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get("session")
        interaction_type = request.data.get("interaction_type")
        content = request.data.get("content", "")
        file_url = request.data.get("file_url", "")

        if not session_id or not interaction_type:
            return Response({"success": False, "message": "session and interaction_type required"}, status=400)

        interaction = TelemedicineInteraction.objects.create(
            session_id=session_id,
            sender=request.user,
            interaction_type=interaction_type,
            content=content,
            file_url=file_url,
        )
        result = TelemedicineInteractionSerializer(interaction)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)
