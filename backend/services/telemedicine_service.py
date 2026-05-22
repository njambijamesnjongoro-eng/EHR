from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import TelemedicineSession, TelemedicineRecording, User, Patient
from events.event_bus import EventBus


class TelemedicineExpansionService:
    """Expanded telemedicine service with virtual workflows and session tracking."""

    @staticmethod
    def create_session(patient, doctor, hospital, scheduled_at, session_type="video", meeting_url="") -> TelemedicineSession:
        import secrets
        if not meeting_url:
            meeting_url = f"https://telemed.example.com/room/{secrets.token_urlsafe(16)}"

        session = TelemedicineSession.objects.create(
            patient=patient,
            doctor=doctor,
            hospital=hospital,
            scheduled_at=scheduled_at,
            session_type=session_type,
            meeting_url=meeting_url,
        )

        EventBus.emit_clinical(
            event_type="telemedicine.session_scheduled",
            data={
                "session_id": session.id,
                "patient_id": patient.id,
                "doctor_id": doctor.id,
                "hospital_id": hospital.id,
                "scheduled_at": scheduled_at.isoformat(),
                "session_type": session_type,
            },
            aggregate_type="TelemedicineSession",
            aggregate_id=str(session.id),
        )

        return session

    @staticmethod
    def start_session(session_id: int) -> TelemedicineSession:
        session = TelemedicineSession.objects.get(id=session_id)
        session.status = TelemedicineSession.SessionStatus.IN_PROGRESS
        session.started_at = timezone.now()
        session.save(update_fields=["status", "started_at"])

        EventBus.emit_clinical(
            event_type="telemedicine.session_started",
            data={"session_id": session.id},
            aggregate_type="TelemedicineSession",
            aggregate_id=str(session.id),
        )

        return session

    @staticmethod
    def complete_session(session_id: int, consultation_notes: str = "") -> TelemedicineSession:
        session = TelemedicineSession.objects.get(id=session_id)
        session.status = TelemedicineSession.SessionStatus.COMPLETED
        session.ended_at = timezone.now()
        if consultation_notes:
            session.consultation_notes = consultation_notes
        session.save(update_fields=["status", "ended_at", "consultation_notes"])

        EventBus.emit_clinical(
            event_type="telemedicine.session_completed",
            data={"session_id": session.id, "duration_minutes": TelemedicineExpansionService._duration_minutes(session)},
            aggregate_type="TelemedicineSession",
            aggregate_id=str(session.id),
        )

        return session

    @staticmethod
    def cancel_session(session_id: int, reason: str = "") -> TelemedicineSession:
        session = TelemedicineSession.objects.get(id=session_id)
        session.status = TelemedicineSession.SessionStatus.CANCELLED
        session.cancellation_reason = reason
        session.save(update_fields=["status", "cancellation_reason"])

        EventBus.emit_clinical(
            event_type="telemedicine.session_cancelled",
            data={"session_id": session.id, "reason": reason},
            aggregate_type="TelemedicineSession",
            aggregate_id=str(session.id),
        )

        return session

    @staticmethod
    def get_doctor_schedule(doctor_id: int, date_from=None, date_to=None) -> list:
        qs = TelemedicineSession.objects.filter(doctor_id=doctor_id)
        if date_from:
            qs = qs.filter(scheduled_at__gte=date_from)
        if date_to:
            qs = qs.filter(scheduled_at__lte=date_to)
        return qs.order_by("scheduled_at")

    @staticmethod
    def get_patient_sessions(patient_id: int) -> list:
        return TelemedicineSession.objects.filter(patient_id=patient_id).order_by("-scheduled_at")

    @staticmethod
    def get_hospital_sessions(hospital_id: int, status: str = None, days: int = 7) -> list:
        qs = TelemedicineSession.objects.filter(
            hospital_id=hospital_id,
            scheduled_at__gte=timezone.now() - timedelta(days=days),
        )
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-scheduled_at")

    @staticmethod
    def add_recording(session_id: int, recording_type: str, file_url: str = "", duration_seconds: int = 0) -> TelemedicineRecording:
        return TelemedicineRecording.objects.create(
            session_id=session_id,
            recording_type=recording_type,
            file_url=file_url,
            duration_seconds=duration_seconds,
        )

    @staticmethod
    def _duration_minutes(session) -> int:
        if session.started_at and session.ended_at:
            return int((session.ended_at - session.started_at).total_seconds() / 60)
        return 0

    @staticmethod
    def get_session_statistics(hospital_id: int = None, days: int = 30) -> dict:
        since = timezone.now() - timedelta(days=days)
        qs = TelemedicineSession.objects.filter(scheduled_at__gte=since)
        if hospital_id:
            qs = qs.filter(hospital_id=hospital_id)

        total = qs.count()
        completed = qs.filter(status=TelemedicineSession.SessionStatus.COMPLETED).count()
        cancelled = qs.filter(status=TelemedicineSession.SessionStatus.CANCELLED).count()
        missed = qs.filter(status=TelemedicineSession.SessionStatus.MISSED).count()

        return {
            "period_days": days,
            "total_sessions": total,
            "completed": completed,
            "cancelled": cancelled,
            "missed": missed,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "cancellation_rate": round(cancelled / total * 100, 1) if total > 0 else 0,
            "no_show_rate": round(missed / total * 100, 1) if total > 0 else 0,
        }
