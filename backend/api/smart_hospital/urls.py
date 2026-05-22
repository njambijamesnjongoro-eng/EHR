from django.urls import path
from . import views

urlpatterns = [
    path("devices/", views.SmartHospitalDeviceListView.as_view(), name="smart-devices-list"),
    path("devices/<int:pk>/", views.SmartHospitalDeviceDetailView.as_view(), name="smart-devices-detail"),
    path("devices/register/", views.SmartHospitalRegisterView.as_view(), name="smart-devices-register"),
    path("heartbeat/", views.HeartbeatView.as_view(), name="smart-heartbeat"),
    path("hospitals/<int:hospital_id>/bed-occupancy/", views.BedOccupancyView.as_view(), name="smart-bed-occupancy"),
    path("devices/offline/", views.OfflineDevicesView.as_view(), name="smart-devices-offline"),
    # Phase 7 - IoT Events
    path("device-events/", views.SmartDeviceEventListView.as_view(), name="smart-device-events-list"),
    path("device-events/<int:pk>/", views.SmartDeviceEventDetailView.as_view(), name="smart-device-events-detail"),
    path("device-events/ingest/", views.IngestDeviceEventView.as_view(), name="smart-device-events-ingest"),
    path("devices/<int:device_id>/health/", views.DeviceHealthView.as_view(), name="smart-device-health"),
    path("iot-summary/", views.HospitalIoTSummaryView.as_view(), name="smart-iot-summary"),
    # Phase 7 - Automation
    path("automation/patient-flow/", views.PatientFlowAnalysisView.as_view(), name="smart-patient-flow"),
    path("automation/bottlenecks/", views.BottleneckDetectionView.as_view(), name="smart-bottlenecks"),
    path("automation/staffing/", views.PredictiveStaffingView.as_view(), name="smart-staffing"),
    path("automation/equipment/", views.EquipmentUtilizationView.as_view(), name="smart-equipment"),
    # Phase 8 - Metrics & Telemetry
    path("metrics/", views.SmartMetricListView.as_view(), name="smart-metrics-list"),
    path("telemetry/summary/", views.HospitalTelemetrySummaryView.as_view(), name="smart-telemetry-summary"),
    path("telemetry/record/", views.RecordDeviceTelemetryView.as_view(), name="smart-telemetry-record"),
]
