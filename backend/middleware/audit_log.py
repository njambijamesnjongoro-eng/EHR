import json
import time
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from core.models import AuditLog


class AuditLogMiddleware(MiddlewareMixin):
    SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

    def process_request(self, request):
        request._audit_start_time = time.time()

    def process_response(self, request, response):
        if not getattr(settings, "AUDIT_LOG_ENABLED", True):
            return response

        if request.method in self.SAFE_METHODS:
            return response

        if not request.path.startswith("/api/"):
            return response

        if request.path.startswith("/api/auth/login/"):
            return response

        if request.path.startswith("/api/auth/refresh/"):
            return response

        user = request.user if request.user.is_authenticated else None

        resource_type = self._get_resource_type(request.path)
        resource_id = self._get_resource_id(request.path)

        if response.status_code >= 400:
            return response

        try:
            AuditLog.objects.create(
                user=user,
                action=self._map_method_to_action(request.method),
                resource_type=resource_type,
                resource_id=resource_id,
                description=f"{request.method} {request.path} - {response.status_code}",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                request_method=request.method,
                request_path=request.path,
                response_status=response.status_code,
            )
        except Exception:
            pass

        return response

    def _map_method_to_action(self, method):
        mapping = {
            "POST": AuditLog.Action.CREATE,
            "PUT": AuditLog.Action.UPDATE,
            "PATCH": AuditLog.Action.UPDATE,
            "DELETE": AuditLog.Action.DELETE,
        }
        return mapping.get(method, AuditLog.Action.READ)

    def _get_resource_type(self, path):
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            return f"{parts[0]}_{parts[1]}"
        return parts[0] if parts else "unknown"

    def _get_resource_id(self, path):
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 5:
            return parts[4]
        if len(parts) >= 3:
            return parts[2]
        return None
