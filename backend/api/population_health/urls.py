from django.urls import path
from . import views

urlpatterns = [
    path("insights/", views.PopulationInsightList.as_view(), name="population-insights-list"),
    path("insights/record/", views.RecordInsight.as_view(), name="population-insights-record"),
    path("disease-burden/", views.DiseaseBurden.as_view(), name="population-disease-burden"),
    path("healthcare-access/", views.HealthcareAccess.as_view(), name="population-healthcare-access"),
    path("health-equity/", views.HealthEquity.as_view(), name="population-health-equity"),
    path("regional-comparison/", views.RegionalComparison.as_view(), name="population-regional-comparison"),
    path("forecasts/", views.PredictiveForecastList.as_view(), name="population-forecasts-list"),
    path("forecasts/record/", views.RecordForecast.as_view(), name="population-forecasts-record"),
]
