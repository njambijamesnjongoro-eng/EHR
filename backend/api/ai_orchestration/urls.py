from django.urls import path
from . import views

urlpatterns = [
    path("models/", views.ModelRegistryList.as_view(), name="ai-models-list"),
    path("models/<int:pk>/", views.ModelRegistryDetail.as_view(), name="ai-models-detail"),
    path("models/<int:pk>/status/", views.UpdateModelStatus.as_view(), name="ai-models-status"),
    path("models/<int:pk>/audit/", views.AIAuditTrail.as_view(), name="ai-models-audit"),
    path("governance-report/", views.ModelGovernanceReport.as_view(), name="ai-governance-report"),
]
