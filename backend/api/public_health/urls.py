from django.urls import path
from . import views

urlpatterns = [
    path("metrics/", views.PublicHealthMetricListView.as_view(), name="public-health-metrics"),
    path("disease-prevalence/", views.DiseasePrevalenceView.as_view(), name="public-health-disease-prevalence"),
    path("outbreak-signals/", views.OutbreakSignalView.as_view(), name="public-health-outbreak-signals"),
    path("county-heatmap/", views.CountyHeatmapView.as_view(), name="public-health-county-heatmap"),
    path("healthcare-burden/", views.HealthcareBurdenView.as_view(), name="public-health-healthcare-burden"),
    path("vaccination-analytics/", views.VaccinationAnalyticsView.as_view(), name="public-health-vaccination"),
    path("mortality-trends/", views.MortalityTrendsView.as_view(), name="public-health-mortality"),
    # Phase 7 - Forecasts
    path("disease-forecast/", views.DiseaseForecastView.as_view(), name="public-health-disease-forecast"),
]
