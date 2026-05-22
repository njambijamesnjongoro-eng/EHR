from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"requests", views.ImagingRequestViewSet, basename="imaging-request")
router.register(r"results", views.ImagingResultViewSet, basename="imaging-result")

urlpatterns = [path("", include(router.urls))]
