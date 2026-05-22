from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Visit, VitalSign, Diagnosis, Prescription, AuditLog
from core.permissions import IsDoctor, IsStaff, IsNurse
from .serializers import (
    VisitListSerializer,
    VisitDetailSerializer,
    VisitCreateSerializer,
    VisitUpdateSerializer,
    VitalSignSerializer,
    DiagnosisSerializer,
    PrescriptionSerializer,
    PrescriptionDispenseSerializer,
)


# ─── Visit ViewSet ───
class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.select_related("patient", "doctor").all()
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "patient__health_id",
        "chief_complaint",
        "diagnosis_summary",
    ]
    ordering_fields = ["visit_date", "created_at", "status"]
    ordering = ["-visit_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return VisitListSerializer
        if self.action == "create":
            return VisitCreateSerializer
        if self.action in ("update", "partial_update"):
            return VisitUpdateSerializer
        return VisitDetailSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsDoctor()]
        if self.action in ("update", "partial_update"):
            return [IsAuthenticated(), IsDoctor()]
        return [IsAuthenticated(), IsStaff()]

    def perform_create(self, serializer):
        visit = serializer.save()

        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            resource_type="visit",
            resource_id=str(visit.id),
            description=f"Created visit for patient {visit.patient.health_id}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/clinical/visits/",
        )

    def perform_update(self, serializer):
        visit = serializer.save()

        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.Action.UPDATE,
            resource_type="visit",
            resource_id=str(visit.id),
            description=f"Updated visit {visit.id} for patient {visit.patient.health_id}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path=f"/api/clinical/visits/{visit.id}/",
        )

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        visit = self.get_object()
        visit.status = Visit.Status.COMPLETED
        visit.save(update_fields=["status", "updated_at"])

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            resource_type="visit",
            resource_id=str(visit.id),
            description=f"Closed visit {visit.id}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path=f"/api/clinical/visits/{pk}/close/",
        )

        return Response(
            {"success": True, "message": "Visit closed successfully"},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        visit = self.get_object()
        patient = visit.patient
        from django.utils import timezone
        import datetime

        events = []

        visit_data = {
            "type": "visit",
            "id": visit.id,
            "title": f"Visit - {visit.visit_date.date()}",
            "description": visit.chief_complaint,
            "status": visit.status,
            "date": visit.visit_date.isoformat(),
        }
        events.append(visit_data)

        for dx in visit.diagnoses.all():
            events.append({
                "type": "diagnosis",
                "id": dx.id,
                "title": dx.diagnosis_name,
                "description": f"Severity: {dx.severity}",
                "icd_code": dx.icd_code,
                "date": dx.diagnosed_at.isoformat(),
            })

        for rx in visit.prescriptions.all():
            events.append({
                "type": "prescription",
                "id": rx.id,
                "title": f"{rx.medication_name} {rx.dosage}",
                "description": f"{rx.frequency} - {rx.route}",
                "dispensed": rx.is_dispensed,
                "date": rx.prescribed_at.isoformat(),
            })

        for lab in visit.lab_requests.all():
            lab_data = {
                "type": "lab_request",
                "id": lab.id,
                "title": lab.test_name,
                "description": lab.status,
                "priority": lab.priority,
                "date": lab.requested_at.isoformat(),
            }
            events.append(lab_data)
            if hasattr(lab, "result") and lab.result:
                events.append({
                    "type": "lab_result",
                    "id": lab.result.id,
                    "title": f"Result: {lab.test_name}",
                    "description": lab.result.remarks or "Completed",
                    "is_abnormal": lab.result.is_abnormal,
                    "date": lab.result.result_at.isoformat(),
                })

        events.sort(key=lambda e: e["date"], reverse=True)

        return Response({"success": True, "data": events})


# ─── Vital Signs ViewSet ───
class VitalSignViewSet(viewsets.ModelViewSet):
    queryset = VitalSign.objects.select_related("patient", "recorded_by").all()
    serializer_class = VitalSignSerializer
    ordering = ["-recorded_at"]

    def get_permissions(self):
        if self.action in ("create",):
            return [IsAuthenticated(), IsNurse()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsDoctor()]
        return [IsAuthenticated(), IsStaff()]

    def perform_create(self, serializer):
        vital = serializer.save()

        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            resource_type="vital_sign",
            resource_id=str(vital.id),
            description=f"Recorded vitals for patient {vital.patient.health_id}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/clinical/vitals/",
        )


# ─── Diagnosis ViewSet ───
class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.select_related("patient", "diagnosed_by").all()
    serializer_class = DiagnosisSerializer
    search_fields = ["diagnosis_name", "icd_code", "clinical_notes"]
    ordering_fields = ["diagnosed_at", "severity"]
    ordering = ["-diagnosed_at"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsDoctor()]
        return [IsAuthenticated(), IsStaff()]

    def perform_create(self, serializer):
        diagnosis = serializer.save()

        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            resource_type="diagnosis",
            resource_id=str(diagnosis.id),
            description=f"Diagnosis: {diagnosis.diagnosis_name} for patient {diagnosis.patient.health_id}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/clinical/diagnoses/",
        )

    def perform_update(self, serializer):
        diagnosis = serializer.save()

        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.Action.UPDATE,
            resource_type="diagnosis",
            resource_id=str(diagnosis.id),
            description=f"Updated diagnosis {diagnosis.diagnosis_name}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path=f"/api/clinical/diagnoses/{diagnosis.id}/",
        )


# ─── Prescription ViewSet ───
class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.select_related("patient", "prescribed_by").all()
    serializer_class = PrescriptionSerializer
    search_fields = ["medication_name"]
    ordering_fields = ["prescribed_at"]
    ordering = ["-prescribed_at"]

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsDoctor()]
        if self.action == "dispense":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated(), IsStaff()]

    def perform_create(self, serializer):
        rx = serializer.save()

        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            resource_type="prescription",
            resource_id=str(rx.id),
            description=f"Prescribed {rx.medication_name} {rx.dosage} for patient {rx.patient.health_id}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/clinical/prescriptions/",
        )

    @action(detail=False, methods=["post"])
    def dispense(self, request):
        serializer = PrescriptionDispenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data["prescription_ids"]
        updated = Prescription.objects.filter(id__in=ids).update(
            is_dispensed=True,
            dispensed_at=timezone.now(),
            dispensed_by=request.user,
        )

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            resource_type="prescription",
            resource_id=",".join(str(i) for i in ids),
            description=f"Dispensed {updated} prescriptions",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path="/api/clinical/prescriptions/dispense/",
        )

        return Response(
            {
                "success": True,
                "message": f"{updated} prescriptions marked as dispensed",
            },
            status=status.HTTP_200_OK,
        )
