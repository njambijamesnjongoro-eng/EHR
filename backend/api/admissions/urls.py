from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"wards", views.WardViewSet, basename="ward")
router.register(r"beds", views.BedViewSet, basename="bed")
router.register(r"admissions", views.AdmissionViewSet, basename="admission")

urlpatterns = [path("", include(router.urls))]
