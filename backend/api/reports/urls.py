from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.DashboardStatsView.as_view(), name="report-dashboard"),
    path("revenue/", views.RevenueReportView.as_view(), name="report-revenue"),
    path("clinical/", views.ClinicalReportView.as_view(), name="report-clinical"),
]
