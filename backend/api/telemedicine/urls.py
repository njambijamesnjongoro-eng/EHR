from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"sessions", views.TelemedicineSessionViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("statistics/", views.TelemedicineStatisticsView.as_view(), name="telemed-statistics"),
    path("doctor-schedule/", views.DoctorScheduleView.as_view(), name="telemed-doctor-schedule"),
    # Phase 7 - Interactions
    path("interactions/", views.TelemedicineInteractionListView.as_view(), name="telemed-interactions-list"),
    path("interactions/create/", views.TelemedicineInteractionCreateView.as_view(), name="telemed-interactions-create"),
]
