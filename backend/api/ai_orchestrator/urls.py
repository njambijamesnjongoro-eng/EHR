from django.urls import path
from . import views

urlpatterns = [
    path("recommendations/", views.AIRecommendationListView.as_view(), name="ai-orch-recommendations-list"),
    path("recommendations/<int:pk>/", views.AIRecommendationDetailView.as_view(), name="ai-orch-recommendations-detail"),
    path("recommendations/<int:pk>/accept/", views.AIRecommendationAcceptView.as_view(), name="ai-orch-recommendations-accept"),
    path("recommendations/<int:pk>/reject/", views.AIRecommendationRejectView.as_view(), name="ai-orch-recommendations-reject"),
    path("generate-clinical/", views.GenerateClinicalRecommendationView.as_view(), name="ai-orch-generate-clinical"),
    path("generate-preventive/", views.GeneratePreventiveRecommendationView.as_view(), name="ai-orch-generate-preventive"),
    path("workflow-optimization/", views.WorkflowOptimizationView.as_view(), name="ai-orch-workflow-optimization"),
]
