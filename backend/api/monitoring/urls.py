from django.urls import path
from . import views

urlpatterns = [
    path("metrics/", views.SystemHealthMetricListView.as_view(), name="monitoring-metrics-list"),
    path("dashboard/", views.SystemHealthDashboardView.as_view(), name="monitoring-dashboard"),
    path("health/", views.HealthCheckAPIView.as_view(), name="monitoring-health"),
    path("prometheus/", views.PrometheusMetricsView.as_view(), name="monitoring-prometheus"),
    path("infrastructure/health/", views.InfrastructureHealthView.as_view(), name="monitoring-infra-health"),
    path("infrastructure/recommendations/", views.OptimizationRecommendationsView.as_view(), name="monitoring-infra-recommendations"),
    path("infrastructure/self-heal/", views.SelfHealingView.as_view(), name="monitoring-infra-self-heal"),
    path("events/", views.EventStreamListView.as_view(), name="monitoring-events"),
    # Phase 8 - Twin Monitoring
    path("twins/", views.TwinMonitorListView.as_view(), name="monitoring-twins-list"),
    path("twins/<int:pk>/", views.TwinDetailView.as_view(), name="monitoring-twins-detail"),
]
