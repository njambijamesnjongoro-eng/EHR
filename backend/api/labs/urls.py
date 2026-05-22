from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"requests", views.LabRequestViewSet, basename="lab-request")
router.register(r"results", views.LabResultViewSet, basename="lab-result")

urlpatterns = [
    path("", include(router.urls)),
]
