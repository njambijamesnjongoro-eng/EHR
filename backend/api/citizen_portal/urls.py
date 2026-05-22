from django.urls import path
from . import views

urlpatterns = [
    path("health-summary/", views.HealthSummaryView.as_view(), name="citizen-health-summary"),
    path("profile/", views.ProfileView.as_view(), name="citizen-profile"),
    path("appointments/", views.MyAppointmentsView.as_view(), name="citizen-appointments"),
    path("prescriptions/", views.MyPrescriptionsView.as_view(), name="citizen-prescriptions"),
    path("wearable-devices/", views.MyWearableDevicesView.as_view(), name="citizen-wearable-devices"),
    path("readings/", views.MyReadingsView.as_view(), name="citizen-readings"),
    # Phase 7 - Citizen Super Portal
    path("full-health-record/", views.FullHealthRecordView.as_view(), name="citizen-full-health-record"),
    path("emergency-profile/", views.EmergencyProfileView.as_view(), name="citizen-emergency-profile"),
    path("share-data/", views.ShareHealthDataView.as_view(), name="citizen-share-data"),
    path("care-reminders/", views.CareRemindersView.as_view(), name="citizen-care-reminders"),
    # Phase 8 - Extended Monitoring
    path("telemetry/", views.MyTelemetryView.as_view(), name="citizen-telemetry"),
    path("population-insights/", views.MyPopulationInsightsView.as_view(), name="citizen-population-insights"),
]
