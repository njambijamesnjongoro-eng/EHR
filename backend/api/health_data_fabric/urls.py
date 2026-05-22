from django.urls import path
from . import views

urlpatterns = [
    path("events/", views.EventStreamListView.as_view(), name="data-fabric-events"),
    path("events/emit/", views.EmitEventView.as_view(), name="data-fabric-events-emit"),
    path("events/chain/", views.EventChainView.as_view(), name="data-fabric-events-chain"),
    path("events/correlate/", views.CorrelateEventsView.as_view(), name="data-fabric-events-correlate"),
    path("events/metrics/", views.EventMetricsView.as_view(), name="data-fabric-events-metrics"),
    path("infrastructure/", views.InfrastructureEventListView.as_view(), name="data-fabric-infrastructure"),
    path("infrastructure/<int:pk>/", views.InfrastructureEventDetailView.as_view(), name="data-fabric-infrastructure-detail"),
    path("infrastructure/log/", views.LogInfrastructureEventView.as_view(), name="data-fabric-infrastructure-log"),
    path("infrastructure/errors/", views.RecentErrorsView.as_view(), name="data-fabric-infrastructure-errors"),
    path("predictions/record/", views.RecordPredictionView.as_view(), name="data-fabric-predictions-record"),
]
