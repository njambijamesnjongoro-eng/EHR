from django.urls import path
from . import views

urlpatterns = [
    path("events/", views.EmergencyEventList.as_view(), name="emergency-events-list"),
    path("events/<int:pk>/", views.EmergencyEventDetail.as_view(), name="emergency-events-detail"),
    path("events/<int:pk>/status/", views.UpdateStatus.as_view(), name="emergency-events-status"),
    path("active/", views.ActiveEmergencies.as_view(), name="emergency-active"),
    path("regional-capacity/", views.RegionalCapacity.as_view(), name="emergency-regional-capacity"),
    path("national-overview/", views.NationalOverview.as_view(), name="emergency-national-overview"),
]
