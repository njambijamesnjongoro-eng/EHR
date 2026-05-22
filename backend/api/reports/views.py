from datetime import timedelta
from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    Patient, Admission, Visit, Invoice, Payment,
    LabRequest, Prescription, Diagnosis, Bed, Ward,
    ImagingRequest,
)
from core.permissions import IsHospitalAdmin


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)

        active_admissions = Admission.objects.filter(status=Admission.Status.ACTIVE).count()
        total_beds = Bed.objects.count()
        occupied_beds = Bed.objects.filter(occupancy_status=Bed.Status.OCCUPIED).count()
        available_beds = Bed.objects.filter(occupancy_status=Bed.Status.AVAILABLE).count()
        total_patients = Patient.objects.filter(is_active=True).count()
        total_visits = Visit.objects.count()
        today_visits = Visit.objects.filter(visit_date__date=today).count()

        monthly_revenue = Invoice.objects.filter(
            status=Invoice.Status.PAID,
            created_at__date__gte=month_start,
        ).aggregate(total=Sum("total_amount"))["total"] or 0

        pending_invoices = Invoice.objects.filter(
            status__in=[Invoice.Status.PENDING, Invoice.Status.PARTIALLY_PAID]
        ).count()

        pending_labs = LabRequest.objects.filter(status=LabRequest.Status.REQUESTED).count()
        pending_imaging = ImagingRequest.objects.filter(
            status=ImagingRequest.Status.REQUESTED
        ).count()

        recent_admissions = Admission.objects.filter(
            status=Admission.Status.ACTIVE
        ).select_related("patient", "ward", "bed").order_by("-admission_date")[:10]

        ward_stats = Ward.objects.annotate(
            total_beds=Count("beds"),
            occ_beds=Count("beds", filter=Q(beds__occupancy_status=Bed.Status.OCCUPIED)),
        ).values("ward_name", "ward_type", "total_beds", "occ_beds")

        return Response({
            "success": True,
            "data": {
                "active_admissions": active_admissions,
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "available_beds": available_beds,
                "total_patients": total_patients,
                "total_visits": total_visits,
                "today_visits": today_visits,
                "monthly_revenue": monthly_revenue,
                "pending_invoices": pending_invoices,
                "pending_labs": pending_labs,
                "pending_imaging": pending_imaging,
                "ward_stats": list(ward_stats),
            },
        })


class RevenueReportView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        invoices = Invoice.objects.filter(created_at__gte=since)
        total_revenue = invoices.aggregate(total=Sum("total_amount"))["total"] or 0
        total_collected = invoices.aggregate(collected=Sum("amount_paid"))["collected"] or 0
        pending = invoices.filter(
            status__in=[Invoice.Status.PENDING, Invoice.Status.PARTIALLY_PAID]
        ).count()

        by_method = (
            Payment.objects.filter(created_at__gte=since)
            .values("payment_method")
            .annotate(total=Sum("amount_paid"))
        )

        return Response({
            "success": True,
            "data": {
                "period_days": days,
                "total_revenue": total_revenue,
                "total_collected": total_collected,
                "pending_invoices": pending,
                "by_payment_method": list(by_method),
            },
        })


class ClinicalReportView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        diagnoses_count = Diagnosis.objects.filter(diagnosed_at__gte=since).count()
        prescriptions_count = Prescription.objects.filter(prescribed_at__gte=since).count()
        lab_requests = LabRequest.objects.filter(requested_at__gte=since).count()
        lab_completed = LabRequest.objects.filter(
            requested_at__gte=since, status=LabRequest.Status.COMPLETED
        ).count()

        top_diagnoses = (
            Diagnosis.objects.filter(diagnosed_at__gte=since)
            .values("diagnosis_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return Response({
            "success": True,
            "data": {
                "period_days": days,
                "diagnoses_count": diagnoses_count,
                "prescriptions_count": prescriptions_count,
                "lab_requests": lab_requests,
                "lab_completed": lab_completed,
                "top_diagnoses": list(top_diagnoses),
            },
        })
