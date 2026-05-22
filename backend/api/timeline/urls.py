from django.urls import path
from . import views

urlpatterns = [
    path(
        "patient/<int:patient_id>/",
        views.PatientTimelineView.as_view(),
        name="patient-timeline",
    ),
]
