from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class EnterpriseRateLimitMiddleware(MiddlewareMixin):
    """Enhanced rate limiting with per-hospital and per-user limits."""

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        user = request.user
        path = request.path_info

        # Skip rate limiting for non-API routes
        if not path.startswith("/api/"):
            return None

        # Super admins have no rate limit
        if user.role == "super_admin":
            return None

        # Per-user rate limit
        user_key = f"rate_limit:user:{user.id}"
        user_limit = getattr(settings, "USER_RATE_LIMIT", 200)
        user_window = 60  # 1 minute

        user_count = cache.get(user_key, 0)
        if user_count >= user_limit:
            return JsonResponse(
                {"success": False, "message": "Rate limit exceeded. Try again later."},
                status=429,
            )
        cache.set(user_key, user_count + 1, user_window)

        # Per-hospital rate limit for API calls
        if user.hospital_id:
            hospital_key = f"rate_limit:hospital:{user.hospital_id}"
            hospital_limit = getattr(settings, "HOSPITAL_RATE_LIMIT", 1000)
            hospital_count = cache.get(hospital_key, 0)
            if hospital_count >= hospital_limit:
                return JsonResponse(
                    {"success": False, "message": "Hospital rate limit exceeded."},
                    status=429,
                )
            cache.set(hospital_key, hospital_count + 1, user_window)

        return None
