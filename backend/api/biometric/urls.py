from django.urls import path
from . import views

urlpatterns = [
    path("identities/", views.BiometricIdentityListView.as_view(), name="biometric-identities-list"),
    path("register/", views.BiometricRegisterView.as_view(), name="biometric-register"),
    path("verify/", views.BiometricVerifyView.as_view(), name="biometric-verify"),
    path("identities/<int:pk>/deactivate/", views.BiometricDeactivateView.as_view(), name="biometric-deactivate"),
    path("my-biometrics/", views.UserBiometricsView.as_view(), name="biometric-my"),
]
