from django.urls import path
from . import views

urlpatterns = [
    path("insights/", views.AIInsightListView.as_view(), name="ai-insights-list"),
    path("insights/<int:pk>/", views.AIInsightDetailView.as_view(), name="ai-insights-detail"),
    path("insights/<int:pk>/review/", views.AIInsightReviewView.as_view(), name="ai-insights-review"),
    path("assess-risk/", views.RiskAssessmentView.as_view(), name="ai-assess-risk"),
    path("check-medications/", views.MedicationCheckView.as_view(), name="ai-check-medications"),
    path("detect-deterioration/", views.DeteriorationDetectionView.as_view(), name="ai-detect-deterioration"),
]
