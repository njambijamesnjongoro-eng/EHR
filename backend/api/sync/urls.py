from django.urls import path
from . import views

urlpatterns = [
    path("push/", views.SyncViewSet.as_view({"post": "push"}), name="sync-push"),
    path("status/", views.SyncViewSet.as_view({"get": "status"}), name="sync-status"),
    path("pending/", views.SyncViewSet.as_view({"get": "pending"}), name="sync-pending"),
    path("logs/", views.SyncViewSet.as_view({"get": "logs"}), name="sync-logs"),
]
