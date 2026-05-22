from django.urls import path
from . import views

urlpatterns = [
    path("systems/", views.ExternalSystemListView.as_view(), name="interop-systems-list"),
    path("systems/<int:pk>/", views.ExternalSystemDetailView.as_view(), name="interop-systems-detail"),
    path("systems/register/", views.ExternalSystemRegisterView.as_view(), name="interop-systems-register"),
    path("fhir/convert/", views.FHIRConversionView.as_view(), name="interop-fhir-convert"),
    path("fhir/import/", views.FHIRImportView.as_view(), name="interop-fhir-import"),
]
