from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AuditLog
from core.permissions import IsSuperAdmin, IsHospitalAdmin
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    ordering_fields = ["created_at", "action", "resource_type"]
    ordering = ["-created_at"]
    search_fields = [
        "action",
        "resource_type",
        "resource_id",
        "description",
        "user__email",
    ]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        action = request.query_params.get("action")
        resource = request.query_params.get("resource_type")
        user_id = request.query_params.get("user_id")

        if action:
            queryset = queryset.filter(action=action)
        if resource:
            queryset = queryset.filter(resource_type=resource)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "data": serializer.data})
