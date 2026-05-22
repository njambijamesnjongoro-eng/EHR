from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.HospitalDashboardView.as_view(), name="analytics-dashboard"),
    path("disease-trends/", views.DiseaseTrendsView.as_view(), name="analytics-disease-trends"),
    path("revenue/", views.RevenueAnalyticsView.as_view(), name="analytics-revenue"),
    path("departments/", views.DepartmentUtilizationView.as_view(), name="analytics-departments"),
    path("national/", views.NationalAggregateView.as_view(), name="analytics-national"),
    path("predictive/hospital-load/", views.PredictiveHospitalLoadView.as_view(), name="analytics-predictive-load"),
    path("predictive/patient-flow/", views.PredictivePatientFlowView.as_view(), name="analytics-predictive-flow"),
    path("predictive/alerts/", views.PredictiveAlertsView.as_view(), name="analytics-predictive-alerts"),
    path("predictive/anomalies/", views.SystemAnomaliesView.as_view(), name="analytics-predictive-anomalies"),
    # Phase 7 - Risk Profiling
    path("risk-trends/", views.RiskProfilingTrendsView.as_view(), name="analytics-risk-trends"),
    path("high-risk-population/", views.HighRiskPopulationView.as_view(), name="analytics-high-risk-population"),
    # Phase 8 - Operational Intelligence
    path("efficiency/", views.HospitalEfficiencyView.as_view(), name="analytics-efficiency"),
    path("resource-allocation/", views.ResourceAllocationView.as_view(), name="analytics-resource-allocation"),
    path("bottlenecks/", views.OperationalBottlenecksView.as_view(), name="analytics-bottlenecks"),
    path("optimization/", views.OptimizationRecommendationsView.as_view(), name="analytics-optimization"),
]
