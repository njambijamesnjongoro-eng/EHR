from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Patient, AuditLog


class PatientTimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(id=patient_id, is_active=True)
        except Patient.DoesNotExist:
            return Response(
                {"success": False, "message": "Patient not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        events = []

        visits = patient.visits.all().prefetch_related(
            "diagnoses", "prescriptions", "lab_requests__result"
        )

        for visit in visits:
            events.append({
                "type": "visit",
                "id": visit.id,
                "title": f"Visit - {visit.visit_date.date()}",
                "description": visit.chief_complaint or "No complaint recorded",
                "status": visit.status,
                "date": visit.visit_date.isoformat(),
                "sort_date": visit.visit_date.isoformat(),
                "visit_id": visit.id,
                "extra": {
                    "doctor": visit.doctor.get_full_name() if visit.doctor else None,
                    "diagnosis_summary": visit.diagnosis_summary,
                },
            })

            for dx in visit.diagnoses.all():
                events.append({
                    "type": "diagnosis",
                    "id": dx.id,
                    "title": dx.diagnosis_name,
                    "description": f"{dx.get_severity_display()} - {dx.icd_code or 'No ICD'}",
                    "date": dx.diagnosed_at.isoformat(),
                    "sort_date": dx.diagnosed_at.isoformat(),
                    "visit_id": visit.id,
                    "extra": {
                        "type": dx.get_diagnosis_type_display(),
                        "confirmed": dx.is_confirmed,
                    },
                })

            for rx in visit.prescriptions.all():
                events.append({
                    "type": "prescription",
                    "id": rx.id,
                    "title": f"{rx.medication_name} {rx.dosage}",
                    "description": f"{rx.get_frequency_display()} - {rx.get_route_display()}",
                    "date": rx.prescribed_at.isoformat(),
                    "sort_date": rx.prescribed_at.isoformat(),
                    "visit_id": visit.id,
                    "extra": {
                        "dispensed": rx.is_dispensed,
                        "duration": f"{rx.duration_days} days" if rx.duration_days else rx.duration_text,
                    },
                })

            for lab in visit.lab_requests.all():
                events.append({
                    "type": "lab_request",
                    "id": lab.id,
                    "title": f"Lab: {lab.test_name}",
                    "description": f"Status: {lab.get_status_display()} - Priority: {lab.get_priority_display()}",
                    "date": lab.requested_at.isoformat(),
                    "sort_date": lab.requested_at.isoformat(),
                    "visit_id": visit.id,
                    "extra": {
                        "status": lab.status,
                        "priority": lab.priority,
                    },
                })

                if hasattr(lab, "result") and lab.result:
                    events.append({
                        "type": "lab_result",
                        "id": lab.result.id,
                        "title": f"Result: {lab.test_name}",
                        "description": lab.result.remarks or "No remarks",
                        "date": lab.result.result_at.isoformat(),
                        "sort_date": lab.result.result_at.isoformat(),
                        "visit_id": visit.id,
                        "extra": {
                            "is_abnormal": lab.result.is_abnormal,
                            "has_file": bool(lab.result.file_attachment),
                        },
                    })

        events.sort(key=lambda e: e["sort_date"], reverse=True)

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.READ,
            resource_type="patient_timeline",
            resource_id=str(patient.id),
            description=f"Viewed medical timeline for patient {patient.health_id}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path=f"/api/timeline/patient/{patient_id}/",
        )

        return Response({"success": True, "data": events})
