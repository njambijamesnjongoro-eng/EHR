from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"success": True, "data": {"count": count}})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response(
            {"success": True, "message": "All notifications marked as read"},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(
            {"success": True, "message": "Notification marked as read"},
            status=status.HTTP_200_OK,
        )
