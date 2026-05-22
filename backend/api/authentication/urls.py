from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="auth-me"),
    path(
        "refresh/",
        views.TokenRefreshViewCustom.as_view(),
        name="auth-refresh",
    ),
    path(
        "change-password/",
        views.ChangePasswordView.as_view(),
        name="auth-change-password",
    ),
    path("users/", views.UserViewSet.as_view({"post": "create", "get": "list"}), name="auth-users"),
]
