from django.urls import path
from . import views

urlpatterns = [
    path("alerts/", views.EpidemicAlertListView.as_view(), name="epidemic-alerts-list"),
    path("alerts/<int:pk>/", views.EpidemicAlertDetailView.as_view(), name="epidemic-alerts-detail"),
    path("alerts/<int:pk>/resolve/", views.ResolveAlertView.as_view(), name="epidemic-alerts-resolve"),
    path("detect-outbreak/", views.DetectOutbreakView.as_view(), name="epidemic-detect-outbreak"),
    path("regional-spread/", views.RegionalSpreadView.as_view(), name="epidemic-regional-spread"),
    path("forecast/", views.EpidemicForecastView.as_view(), name="epidemic-forecast"),
]
