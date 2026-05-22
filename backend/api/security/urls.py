from django.urls import path
from . import views

urlpatterns = [
    path("events/", views.SecurityEventListView.as_view(), name="security-events-list"),
    path("events/<int:pk>/", views.SecurityEventDetailView.as_view(), name="security-events-detail"),
    path("events/<int:pk>/resolve/", views.SecurityEventResolveView.as_view(), name="security-events-resolve"),
    path("devices/", views.DeviceFingerprintListView.as_view(), name="security-devices-list"),
    path("devices/<int:pk>/", views.DeviceFingerprintDetailView.as_view(), name="security-devices-detail"),
    path("devices/<int:pk>/trust/", views.DeviceTrustView.as_view(), name="security-devices-trust"),
    path("mfa/setup/", views.MFASetupView.as_view(), name="security-mfa-setup"),
    path("mfa/verify/", views.MFAVerifyView.as_view(), name="security-mfa-verify"),
    path("mfa/disable/", views.MFADisableView.as_view(), name="security-mfa-disable"),
    path("risk-dashboard/", views.RiskDashboardView.as_view(), name="security-risk-dashboard"),
    path("behavioral-anomaly/<int:user_id>/", views.BehavioralAnomalyView.as_view(), name="security-behavioral-anomaly"),
    path("threat-hunting/", views.ThreatHuntingView.as_view(), name="security-threat-hunting"),
    path("privilege-abuse/", views.PrivilegeAbuseView.as_view(), name="security-privilege-abuse"),
    path("correlated-events/", views.CorrelatedEventsView.as_view(), name="security-correlated-events"),
    path("distributed-audit/", views.DistributedAuditView.as_view(), name="security-distributed-audit"),
    # Phase 7 - Infrastructure Monitoring
    path("infrastructure-events/", views.InfrastructureEventMonitorListView.as_view(), name="security-infrastructure-events"),
    # Phase 8 - Operational & Threat Intelligence
    path("operational-alerts/", views.OperationalAlertListView.as_view(), name="security-operational-alerts"),
    path("threat-intel/", views.ThreatIntelReportView.as_view(), name="security-threat-intel"),
    path("login-anomalies/", views.LoginAnomalyView.as_view(), name="security-login-anomalies"),
    path("privilege-escalation/", views.PrivilegeEscalationView.as_view(), name="security-privilege-escalation"),
]
