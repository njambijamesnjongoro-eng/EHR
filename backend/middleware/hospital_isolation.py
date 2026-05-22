from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class HospitalIsolationMiddleware(MiddlewareMixin):
    """Enforces hospital-level data isolation.

    Adds the user's hospital context to the request for use
    throughout the request lifecycle. Super admins bypass isolation.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not getattr(settings, "ENABLE_HOSPITAL_ISOLATION", True):
            return None

        if not request.user.is_authenticated:
            return None

        if request.user.role == "super_admin":
            request.hospital_context = "all"
            return None

        hospital_id = getattr(request.user, "hospital_id", None)
        request.hospital_context = hospital_id
        return None
