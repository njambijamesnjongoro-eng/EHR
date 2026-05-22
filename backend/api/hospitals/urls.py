from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"hospitals", views.HospitalViewSet)
router.register(r"departments", views.DepartmentViewSet)
router.register(r"staff", views.HospitalStaffViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
