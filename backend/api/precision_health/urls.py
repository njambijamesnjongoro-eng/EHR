from django.urls import path
from . import views

urlpatterns = [
    path("profiles/", views.HealthRiskProfileListView.as_view(), name="precision-profiles-list"),
    path("profiles/<int:pk>/", views.HealthRiskProfileDetailView.as_view(), name="precision-profiles-detail"),
    path("assess-risk/", views.AssessRiskView.as_view(), name="precision-assess-risk"),
    path("patients/<int:patient_id>/risk-summary/", views.PatientRiskSummaryView.as_view(), name="precision-patient-risk-summary"),
    path("high-risk/", views.HighRiskPatientsView.as_view(), name="precision-high-risk"),
    path("risk-trends/", views.RiskTrendsView.as_view(), name="precision-risk-trends"),
]
