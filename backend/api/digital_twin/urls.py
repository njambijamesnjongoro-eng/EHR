from django.urls import path
from . import views

urlpatterns = [
    path("twins/", views.InfrastructureTwinList.as_view(), name="digital-twin-list"),
    path("twins/<int:pk>/", views.InfrastructureTwinDetail.as_view(), name="digital-twin-detail"),
    path("twins/<int:pk>/simulate/", views.RunSimulation.as_view(), name="digital-twin-simulate"),
    path("twins/<int:pk>/status/", views.TwinStatus.as_view(), name="digital-twin-status"),
    path("twins/<int:pk>/scenarios/", views.CreateScenario.as_view(), name="digital-twin-scenarios"),
    path("twins/compare/", views.CompareScenarios.as_view(), name="digital-twin-compare"),
]
