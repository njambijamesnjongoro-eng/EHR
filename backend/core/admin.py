from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Patient, PatientHistory, AuditLog,
    Visit, VitalSign, Diagnosis, Prescription, LabRequest, LabResult,
    Ward, Bed, Admission, Invoice, Payment,
    ImagingRequest, ImagingResult, Notification,
    Hospital, Department, HospitalStaff, PatientIdentity, PatientMergeLog,
    Referral, ReferralDocument, CrossHospitalAccess,
    SyncQueue, SyncLog,
    InsuranceProfile, InsuranceClaim,
    TelemedicineSession, EnterpriseAuditEvent,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "get_full_name", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Info",
            {"fields": ("first_name", "last_name", "phone_number", "role")},
        ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "password1", "password2", "role"),
            },
        ),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "health_id",
        "full_name",
        "gender",
        "date_of_birth",
        "phone_number",
        "created_at",
    )
    list_filter = ("gender", "blood_group", "created_at")
    search_fields = ("health_id", "first_name", "last_name", "national_id", "phone_number")
    readonly_fields = ("health_id", "qr_code", "created_at", "updated_at")


@admin.register(PatientHistory)
class PatientHistoryAdmin(admin.ModelAdmin):
    list_display = ("patient", "record_type", "title", "recorded_by", "recorded_at")
    list_filter = ("record_type", "recorded_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "resource_type", "resource_id")
    list_filter = ("action", "resource_type", "created_at")
    readonly_fields = (
        "user",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
        "request_path",
        "created_at",
    )


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "visit_date", "status")
    list_filter = ("status", "visit_date")
    search_fields = ("patient__health_id", "patient__first_name", "patient__last_name", "chief_complaint")


@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
    list_display = ("patient", "recorded_at", "temperature", "blood_pressure_systolic", "pulse_rate")
    list_filter = ("recorded_at",)


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ("diagnosis_name", "patient", "diagnosis_type", "severity", "icd_code", "diagnosed_at")
    list_filter = ("diagnosis_type", "severity", "diagnosed_at")
    search_fields = ("diagnosis_name", "icd_code")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("medication_name", "dosage", "patient", "is_dispensed", "prescribed_at")
    list_filter = ("is_dispensed", "route", "frequency")
    search_fields = ("medication_name",)


@admin.register(LabRequest)
class LabRequestAdmin(admin.ModelAdmin):
    list_display = ("test_name", "patient", "status", "priority", "requested_at")
    list_filter = ("status", "priority")


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("lab_request", "patient", "is_abnormal", "result_at")
    list_filter = ("is_abnormal",)


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ("ward_name", "ward_type", "capacity", "available_beds", "occupied_beds")


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ("bed_number", "ward", "occupancy_status")
    list_filter = ("occupancy_status", "ward")


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ("patient", "ward", "bed", "status", "admission_date", "discharge_date")
    list_filter = ("status", "ward")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "patient", "total_amount", "amount_paid", "balance", "status")
    list_filter = ("status",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "amount_paid", "payment_method", "payment_date")
    list_filter = ("payment_method",)


@admin.register(ImagingRequest)
class ImagingRequestAdmin(admin.ModelAdmin):
    list_display = ("imaging_type", "patient", "priority", "status", "requested_at")
    list_filter = ("status", "imaging_type", "priority")


@admin.register(ImagingResult)
class ImagingResultAdmin(admin.ModelAdmin):
    list_display = ("imaging_request", "patient", "is_abnormal", "result_at")
    list_filter = ("is_abnormal",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "category", "is_read", "created_at")
    list_filter = ("category", "is_read")


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("hospital_name", "hospital_code", "hospital_type", "county", "is_active")
    list_filter = ("hospital_type", "county", "is_active")
    search_fields = ("hospital_name", "hospital_code")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("department_name", "hospital", "is_active")
    list_filter = ("is_active",)


@admin.register(HospitalStaff)
class HospitalStaffAdmin(admin.ModelAdmin):
    list_display = ("user", "hospital", "staff_role", "is_active")
    list_filter = ("staff_role", "is_active", "hospital")


@admin.register(PatientIdentity)
class PatientIdentityAdmin(admin.ModelAdmin):
    list_display = ("national_health_id", "patient", "id_type", "verified")
    list_filter = ("verified", "id_type")


@admin.register(PatientMergeLog)
class PatientMergeLogAdmin(admin.ModelAdmin):
    list_display = ("merged_into", "merged_from", "merged_by", "created_at")
    readonly_fields = ("merged_data",)


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("patient", "referring_hospital", "receiving_hospital", "priority", "status", "created_at")
    list_filter = ("status", "priority")


@admin.register(CrossHospitalAccess)
class CrossHospitalAccessAdmin(admin.ModelAdmin):
    list_display = ("patient", "requesting_hospital", "is_authorized", "expires_at")
    list_filter = ("is_authorized",)


@admin.register(SyncQueue)
class SyncQueueAdmin(admin.ModelAdmin):
    list_display = ("resource_type", "action", "hospital", "status", "retry_count", "server_timestamp")
    list_filter = ("status", "action")


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ("hospital", "items_processed", "items_failed", "status", "completed_at")
    list_filter = ("status",)


@admin.register(InsuranceProfile)
class InsuranceProfileAdmin(admin.ModelAdmin):
    list_display = ("patient", "provider", "policy_number", "is_active", "verified")
    list_filter = ("provider", "is_active", "verified")


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = ("claim_number", "insurance_profile", "status", "total_amount", "submitted_at")
    list_filter = ("status",)


@admin.register(TelemedicineSession)
class TelemedicineSessionAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "hospital", "scheduled_at", "status")
    list_filter = ("status", "session_type")


@admin.register(EnterpriseAuditEvent)
class EnterpriseAuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "action", "resource_type", "hospital", "severity", "created_at")
    list_filter = ("event_type", "severity")
