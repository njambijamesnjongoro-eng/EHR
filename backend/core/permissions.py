from rest_framework.permissions import BasePermission, SAFE_METHODS

from django.conf import settings


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "super_admin"


class IsHospitalAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            "super_admin",
            "hospital_admin",
        ]


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            "super_admin",
            "hospital_admin",
            "doctor",
        ]


class IsNurse(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            "super_admin",
            "hospital_admin",
            "doctor",
            "nurse",
        ]


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role != "patient"


class IsPatientOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == "patient":
            return obj.created_by == request.user
        return True


class HasRole(BasePermission):
    allowed_roles = []

    def __init__(self, roles=None):
        self.allowed_roles = roles or []

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.allowed_roles


# ─── Phase 4: Enterprise & Hospital-Scoped Permissions ───

class IsNationalAdmin(BasePermission):
    """Super admins with national-level access across all hospitals."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "super_admin"


class IsHospitalStaff(BasePermission):
    """Any active staff member of a hospital."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == "super_admin":
            return True
        return request.user.hospital_id is not None

    def has_object_permission(self, request, view, obj):
        if request.user.role == "super_admin":
            return True
        if hasattr(obj, "hospital"):
            return obj.hospital_id == request.user.hospital_id
        return True


class IsSameHospital(BasePermission):
    """Object-level: only allow access if the object belongs to the user's hospital."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == "super_admin":
            return True
        hospital_id = getattr(request.user, "hospital_id", None)
        if hospital_id is None:
            return False
        obj_hospital_id = getattr(obj, "hospital_id", None)
        if obj_hospital_id is None and hasattr(obj, "hospital"):
            obj_hospital_id = obj.hospital_id
        return obj_hospital_id == hospital_id


class HasStaffRole(BasePermission):
    """Check if user has a specific staff role at their hospital."""
    allowed_staff_roles = []

    def __init__(self, roles=None):
        self.allowed_staff_roles = roles or []

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == "super_admin":
            return True
        if not request.user.hospital_id:
            return False
        from core.models import HospitalStaff
        return HospitalStaff.objects.filter(
            user=request.user,
            hospital_id=request.user.hospital_id,
            staff_role__in=self.allowed_staff_roles,
            is_active=True,
        ).exists()


class CanAccessPatient(BasePermission):
    """Check if the user's hospital has authorized access to a patient record.

    Allows access if:
    - User is super admin
    - Patient belongs to user's hospital
    - There is an active CrossHospitalAccess grant
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == "super_admin":
            return True

        user_hospital_id = request.user.hospital_id
        if not user_hospital_id:
            return False

        patient = self._get_patient(obj)
        if patient is None:
            return True

        if getattr(patient, "hospital_id", None) == user_hospital_id:
            return True

        from core.models import CrossHospitalAccess
        return CrossHospitalAccess.objects.filter(
            patient=patient,
            requesting_hospital_id=user_hospital_id,
            is_authorized=True,
            expires_at__isnull=True,
        ).exists() or CrossHospitalAccess.objects.filter(
            patient=patient,
            requesting_hospital_id=user_hospital_id,
            is_authorized=True,
            expires_at__gte=__import__("django").utils.timezone.now(),
        ).exists()

    def _get_patient(self, obj):
        if hasattr(obj, "patient"):
            return obj.patient
        if isinstance(obj, __import__("core").models.Patient):
            return obj
        return None
