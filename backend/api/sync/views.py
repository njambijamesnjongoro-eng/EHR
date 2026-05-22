from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import SyncQueue, SyncLog
from core.permissions import IsStaff
from services.sync_service import SyncService
from .serializers import (
    SyncQueueSerializer, SyncBatchSerializer,
    SyncLogSerializer, SyncStatusSerializer,
)


class SyncViewSet(viewsets.GenericViewSet):
    queryset = SyncQueue.objects.all()
    serializer_class = SyncQueueSerializer
    permission_classes = [IsAuthenticated, IsStaff]

    @action(detail=False, methods=["post"])
    def push(self, request):
        hospital_id = request.user.hospital_id
        if not hospital_id:
            return Response({"success": False, "message": "No hospital affiliation"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SyncBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data["items"]
        device_id = serializer.validated_data.get("device_id", "")

        for item in items:
            SyncService.enqueue(
                hospital_id=hospital_id,
                resource_type=item["resource_type"],
                resource_id=item.get("resource_id", ""),
                action=item["action"],
                payload=item["payload"],
                device_id=device_id,
                client_timestamp=item.get("client_timestamp"),
            )

        # Process immediately for small batches
        result = SyncService.process_queue(hospital_id, device_id)

        return Response({
            "success": True,
            "data": result,
        })

    @action(detail=False, methods=["get"])
    def status(self, request):
        hospital_id = request.user.hospital_id
        if not hospital_id:
            return Response({"success": False, "message": "No hospital affiliation"}, status=status.HTTP_400_BAD_REQUEST)

        pending = SyncQueue.objects.filter(
            hospital_id=hospital_id,
            status=SyncQueue.SyncStatus.PENDING,
        ).count()
        failed = SyncQueue.objects.filter(
            hospital_id=hospital_id,
            status=SyncQueue.SyncStatus.FAILED,
        ).count()
        last_sync = SyncLog.objects.filter(
            hospital_id=hospital_id,
            status="success",
        ).order_by("-completed_at").first()

        serializer = SyncStatusSerializer(instance={
            "pending_count": pending,
            "failed_count": failed,
            "last_sync": last_sync.completed_at if last_sync else None,
        })
        return Response({"success": True, "data": serializer.data})

    @action(detail=False, methods=["get"])
    def pending(self, request):
        hospital_id = request.user.hospital_id
        items = SyncQueue.objects.filter(
            hospital_id=hospital_id,
            status=SyncQueue.SyncStatus.PENDING,
        ).order_by("client_timestamp")[:100]

        serializer = self.get_serializer(items, many=True)
        return Response({"success": True, "data": serializer.data})

    @action(detail=False, methods=["get"])
    def logs(self, request):
        hospital_id = request.user.hospital_id
        logs = SyncLog.objects.filter(hospital_id=hospital_id).order_by("-completed_at")[:20]
        serializer = SyncLogSerializer(logs, many=True)
        return Response({"success": True, "data": serializer.data})
