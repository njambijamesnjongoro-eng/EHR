from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"profiles", views.InsuranceProfileViewSet)
router.register(r"claims", views.InsuranceClaimViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
