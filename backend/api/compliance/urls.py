from django.urls import path
from . import views

urlpatterns = [
    path("consents/", views.ConsentLogListView.as_view(), name="compliance-consents-list"),
    path("consents/<int:pk>/", views.ConsentLogDetailView.as_view(), name="compliance-consents-detail"),
    path("consents/grant/", views.ConsentGrantView.as_view(), name="compliance-consents-grant"),
    path("consents/<int:pk>/revoke/", views.ConsentRevokeView.as_view(), name="compliance-consents-revoke"),
    path("audit-events/", views.AuditEventListView.as_view(), name="compliance-audit-list"),
    path("audit-report/", views.AuditReportView.as_view(), name="compliance-audit-report"),
]
