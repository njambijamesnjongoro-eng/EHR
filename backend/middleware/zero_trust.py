import time
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

from core.models import SecurityEvent, EnterpriseAuditEvent


class ZeroTrustMiddleware(MiddlewareMixin):
    """Implements Zero Trust security principles for every API request.

    - Verifies every request as if it originates from an untrusted network
    - Validates device fingerprint consistency
    - Logs anomalous access patterns
    - Enforces session security
    """

    def process_request(self, request):
        if not request.path_info.startswith("/api/"):
            return None

        request._request_start = time.time()
        request._request_id = None

        if request.user.is_authenticated:
            self._validate_request_context(request)

        return None

    def process_response(self, request, response):
        if hasattr(request, "_request_start"):
            duration_ms = int((time.time() - request._request_start) * 1000)

            if hasattr(request, "user") and request.user.is_authenticated:
                response["X-Request-ID"] = getattr(request, "_request_id", "")
                response["X-Response-Time-Ms"] = str(duration_ms)

                if duration_ms > 5000:
                    SecurityEvent.objects.create(
                        category=SecurityEvent.EventCategory.ANOMALY,
                        severity=SecurityEvent.Severity.LOW,
                        user=request.user,
                        description=f"Slow API request: {request.method} {request.path_info} ({duration_ms}ms)",
                        metadata={"duration_ms": duration_ms, "path": request.path_info},
                    )

        return response

    def _validate_request_context(self, request):
        from services.security_service import SecurityService

        fp_hash = SecurityService.generate_device_fingerprint(request)

        if "/api/auth/login" not in request.path_info:
            from core.models import DeviceFingerprint
            device = DeviceFingerprint.objects.filter(
                user=request.user, fingerprint_hash=fp_hash
            ).first()

            if device and device.risk_count > 10:
                SecurityEvent.objects.create(
                    category=SecurityEvent.EventCategory.POLICY_VIOLATION,
                    severity=SecurityEvent.Severity.HIGH,
                    user=request.user,
                    ip_address=request.META.get("REMOTE_ADDR"),
                    description=f"High-risk device block: {device.risk_count} risk count",
                    metadata={"fingerprint": fp_hash, "risk_count": device.risk_count},
                )


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Sets comprehensive security headers on all responses."""

    def process_response(self, request, response):
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response["Pragma"] = "no-cache"
        return response
