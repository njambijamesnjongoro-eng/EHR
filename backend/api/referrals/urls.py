from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"referrals", views.ReferralViewSet)
router.register(r"documents", views.ReferralDocumentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
