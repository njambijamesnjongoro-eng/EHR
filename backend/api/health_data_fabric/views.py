from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import InfrastructureEvent, EventStreamLog, PredictiveMetric
from core.permissions import IsSuperAdmin, IsHospitalAdmin
from events.orchestrator import EventOrchestrator
from events.event_bus import EventBus
from services.autonomous_operations_service import AutonomousOperationsService

from .serializers import (
    InfrastructureEventSerializer, EventStreamLogSerializer, PredictiveMetricSerializer,
)


class InfrastructureEventListView(generics.ListAPIView):
    serializer_class = InfrastructureEventSerializer
    filterset_fields = ["event_type", "severity", "service_name", "resolved"]
    ordering = ["-occurred_at"]

    def get_queryset(self):
        return InfrastructureEvent.objects.all()


class InfrastructureEventDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = InfrastructureEventSerializer
    queryset = InfrastructureEvent.objects.all()


class EventStreamListView(generics.ListAPIView):
    serializer_class = EventStreamLogSerializer
    filterset_fields = ["event_source", "event_type", "aggregate_type"]
    ordering = ["-occurred_at"]

    def get_queryset(self):
        return EventStreamLog.objects.all()


class EventChainView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        correlation_id = request.query_params.get("correlation_id")
        if not correlation_id:
            return Response({"success": False, "message": "correlation_id required"}, status=400)
        chain = EventOrchestrator.get_event_chain(correlation_id)
        return Response({"success": True, "data": chain})


class CorrelateEventsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        aggregate_type = request.query_params.get("aggregate_type")
        aggregate_id = request.query_params.get("aggregate_id")
        if not aggregate_type or not aggregate_id:
            return Response({"success": False, "message": "aggregate_type and aggregate_id required"}, status=400)
        data = EventOrchestrator.correlate_events(aggregate_type, aggregate_id)
        return Response({"success": True, "data": data})


class EventMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        hours = int(request.query_params.get("hours", 24))
        data = EventOrchestrator.count_events_by_source(hours)
        return Response({"success": True, "data": data})


class RecentErrorsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        hours = int(request.query_params.get("hours", 1))
        errors = EventOrchestrator.get_recent_errors(hours)
        return Response({
            "success": True,
            "data": InfrastructureEventSerializer(errors, many=True).data,
        })


class EmitEventView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        event_source = request.data.get("event_source")
        event_type = request.data.get("event_type")
        data = request.data.get("data", {})
        if not event_source or not event_type:
            return Response({"success": False, "message": "event_source and event_type required"}, status=400)
        event = EventBus.emit(
            event_source=event_source,
            event_type=event_type,
            data=data,
            aggregate_type=request.data.get("aggregate_type", ""),
            aggregate_id=request.data.get("aggregate_id", ""),
            correlation_id=request.data.get("correlation_id", ""),
        )
        return Response({"success": True, "data": EventStreamLogSerializer(event).data}, status=status.HTTP_201_CREATED)


class LogInfrastructureEventView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        event = AutonomousOperationsService.log_infrastructure_event(
            event_type=request.data.get("event_type"),
            severity=request.data.get("severity", "info"),
            message=request.data.get("message", ""),
            service=request.data.get("service_name", ""),
            host=request.data.get("host_name", ""),
            metrics=request.data.get("metric_data", {}),
            auto_action=request.data.get("auto_action_taken", ""),
        )
        result = InfrastructureEventSerializer(event)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class RecordPredictionView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        metric = AutonomousOperationsService.record_prediction(
            metric_category=request.data.get("metric_category"),
            metric_name=request.data.get("metric_name"),
            predicted_value=request.data.get("predicted_value"),
            hospital_id=request.data.get("hospital"),
            county=request.data.get("county", ""),
            confidence_lower=request.data.get("confidence_interval_lower"),
            confidence_upper=request.data.get("confidence_interval_upper"),
            horizon=int(request.data.get("forecast_horizon_days", 7)),
            model=request.data.get("model_name", ""),
            features=request.data.get("features_used", []),
        )
        return Response({
            "success": True,
            "data": PredictiveMetricSerializer(metric).data,
        }, status=status.HTTP_201_CREATED)
