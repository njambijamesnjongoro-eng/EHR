from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"visits", views.VisitViewSet, basename="visit")
router.register(r"vitals", views.VitalSignViewSet, basename="vital-sign")
router.register(r"diagnoses", views.DiagnosisViewSet, basename="diagnosis")
router.register(r"prescriptions", views.PrescriptionViewSet, basename="prescription")

urlpatterns = [
    path("", include(router.urls)),
]
