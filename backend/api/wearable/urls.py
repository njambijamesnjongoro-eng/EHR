from django.urls import path
from . import views

urlpatterns = [
    path("devices/", views.WearableDeviceListView.as_view(), name="wearable-devices-list"),
    path("devices/<int:pk>/", views.WearableDeviceDetailView.as_view(), name="wearable-devices-detail"),
    path("devices/register/", views.WearableRegisterView.as_view(), name="wearable-devices-register"),
    path("devices/<int:pk>/verify/", views.WearableVerifyView.as_view(), name="wearable-devices-verify"),
    path("readings/", views.DeviceReadingListView.as_view(), name="wearable-readings-list"),
    path("readings/ingest/", views.DeviceReadingIngestView.as_view(), name="wearable-readings-ingest"),
    path("readings/bulk-ingest/", views.DeviceReadingBulkIngestView.as_view(), name="wearable-readings-bulk"),
    path("patients/<int:patient_id>/readings/", views.PatientLatestReadingsView.as_view(), name="wearable-patient-readings"),
]
