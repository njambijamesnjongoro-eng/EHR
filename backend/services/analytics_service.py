from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Avg, Q, F, FloatField
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from core.models import (
    Patient, Hospital, Visit, Admission, Invoice, Payment,
    Diagnosis, LabRequest, ImagingRequest, Referral,
)


class AnalyticsService:
    """Enterprise analytics and reporting engine."""

    @staticmethod
    def hospital_dashboard(hospital: Hospital, days: int = 30):
        since = timezone.now() - timedelta(days=days)

        patients = Patient.objects.filter(hospital=hospital) if hasattr(Patient, 'hospital') else Patient.objects.none()

        visits = Visit.objects.filter(visit_date__gte=since)
        admissions = Admission.objects.filter(admission_date__gte=since)
        invoices = Invoice.objects.filter(created_at__gte=since)

        total_visits = visits.count()
        active_admissions = Admission.objects.filter(status="active").count()
        total_revenue = invoices.aggregate(s=Sum("total_amount"))["s"] or 0
        total_collected = invoices.aggregate(s=Sum("amount_paid"))["s"] or 0

        diagnoses = Diagnosis.objects.filter(created_at__gte=since)
        top_diagnoses = diagnoses.values("diagnosis_name").annotate(
            count=Count("id")
        ).order_by("-count")[:10]

        return {
            "period_days": days,
            "total_patients": Patient.objects.count(),
            "new_patients": Patient.objects.filter(created_at__gte=since).count(),
            "total_visits": total_visits,
            "daily_avg_visits": round(total_visits / max(days, 1), 1),
            "active_admissions": active_admissions,
            "admissions_period": admissions.count(),
            "total_revenue": float(total_revenue),
            "total_collected": float(total_collected),
            "outstanding": float(total_revenue - total_collected),
            "top_diagnoses": list(top_diagnoses),
        }

    @staticmethod
    def disease_trends(days: int = 365):
        since = timezone.now() - timedelta(days=days)
        trends = (
            Diagnosis.objects.filter(created_at__gte=since)
            .annotate(month=TruncMonth("created_at"))
            .values("month", "diagnosis_name")
            .annotate(count=Count("id"))
            .order_by("month", "-count")
        )
        return list(trends)

    @staticmethod
    def revenue_analysis(hospital=None, months: int = 12):
        since = timezone.now() - timedelta(days=months * 30)
        qs = Invoice.objects.filter(created_at__gte=since)
        if hospital:
            qs = qs.filter(visit__hospital=hospital)

        monthly = (
            qs.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(
                total=Sum("total_amount"),
                collected=Sum("amount_paid"),
                count=Count("id"),
            )
            .order_by("month")
        )

        return {
            "monthly": [
                {
                    "month": m["month"].strftime("%Y-%m") if m["month"] else "",
                    "total": float(m["total"] or 0),
                    "collected": float(m["collected"] or 0),
                    "count": m["count"],
                }
                for m in monthly
            ],
            "total_revenue": float(qs.aggregate(s=Sum("total_amount"))["s"] or 0),
            "total_collected": float(qs.aggregate(s=Sum("amount_paid"))["s"] or 0),
        }

    @staticmethod
    def department_utilization(hospital: Hospital):
        departments = hospital.departments.annotate(
            staff_count=Count("staff"),
            active_visits=Count(
                "staff__user__visit_set",
                filter=Q(staff__user__visit_set__status="in_progress"),
            ),
        ).values("department_name", "staff_count", "active_visits")

        return list(departments)

    @staticmethod
    def national_aggregate():
        return {
            "total_hospitals": Hospital.objects.filter(is_active=True).count(),
            "total_patients": Patient.objects.count(),
            "total_visits": Visit.objects.count(),
            "total_referrals": Referral.objects.count(),
            "active_admissions": Admission.objects.filter(status="active").count(),
            "hospitals_by_county": list(
                Hospital.objects.filter(is_active=True)
                .values("county")
                .annotate(count=Count("id"))
                .order_by("-count")
            ),
        }
