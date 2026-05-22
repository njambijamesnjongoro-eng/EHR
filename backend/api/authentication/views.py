from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.throttling import AnonRateThrottle

from core.models import User, AuditLog
from core.permissions import IsSuperAdmin, IsHospitalAdmin
from .serializers import (
    LoginSerializer,
    UserSerializer,
    UserCreateSerializer,
    ChangePasswordSerializer,
)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request=request, email=email, password=password)

        if user is None:
            AuditLog.objects.create(
                action=AuditLog.Action.LOGIN_FAILED,
                resource_type="auth",
                description=f"Failed login attempt for {email}",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                request_path="/api/auth/login/",
            )
            return Response(
                {
                    "success": False,
                    "message": "Invalid email or password",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"success": False, "message": "Account is deactivated"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.LOGIN,
            resource_type="auth",
            description=f"User {user.email} logged in",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            request_path="/api/auth/login/",
        )

        return Response(
            {
                "success": True,
                "message": "Login successful",
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data,
                },
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            AuditLog.objects.create(
                user=request.user,
                action=AuditLog.Action.LOGOUT,
                resource_type="auth",
                description=f"User {request.user.email} logged out",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                request_path="/api/auth/logout/",
            )

            return Response(
                {"success": True, "message": "Logout successful"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "success": True,
                "data": UserSerializer(request.user).data,
            }
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"success": False, "message": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"success": True, "message": "Password changed successfully"},
            status=status.HTTP_200_OK,
        )


class UserViewSet(GenericViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsHospitalAdmin()]
        return [IsAuthenticated()]

    def create(self, request):
        serializer = UserCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.CREATE,
            resource_type="user",
            resource_id=str(user.id),
            description=f"Created user {user.email} with role {user.role}",
            ip_address=request.META.get("REMOTE_ADDR"),
            request_path="/api/auth/users/",
        )

        return Response(
            {
                "success": True,
                "message": "User created successfully",
                "data": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def list(self, request):
        role = request.query_params.get("role")
        queryset = self.get_queryset()
        if role:
            queryset = queryset.filter(role=role)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "data": serializer.data})


class TokenRefreshViewCustom(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return Response(
                {
                    "success": True,
                    "message": "Token refreshed",
                    "data": response.data,
                }
            )
        return Response(
            {"success": False, "message": "Invalid refresh token"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
