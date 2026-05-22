from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BiometricIdentity
from services.biometric_service import BiometricService

from .serializers import (
    BiometricIdentitySerializer, BiometricRegisterSerializer,
    BiometricVerifySerializer,
)


class BiometricIdentityListView(generics.ListAPIView):
    serializer_class = BiometricIdentitySerializer
    filterset_fields = ["user", "biometric_type", "is_active"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return BiometricIdentity.objects.select_related("user").all()


class BiometricRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BiometricRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        identity = BiometricService.register_biometric(
            user=request.user,
            biometric_type=serializer.validated_data["biometric_type"],
            encrypted_template=serializer.validated_data["encrypted_template"],
            device_id=serializer.validated_data.get("device_id", ""),
        )

        result = BiometricIdentitySerializer(identity)
        return Response({"success": True, "data": result.data}, status=status.HTTP_201_CREATED)


class BiometricVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BiometricVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=400)

        valid = BiometricService.verify_biometric(
            user=request.user,
            biometric_type=serializer.validated_data["biometric_type"],
            encrypted_template=serializer.validated_data["encrypted_template"],
        )

        if valid:
            return Response({"success": True, "message": "Biometric verified"})
        return Response({"success": False, "message": "Biometric verification failed"}, status=401)


class BiometricDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        success = BiometricService.deactivate_biometric(pk)
        if success:
            return Response({"success": True, "message": "Biometric deactivated"})
        return Response({"success": False, "message": "Biometric not found"}, status=404)


class UserBiometricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        biometrics = BiometricService.get_user_biometrics(request.user)
        return Response({"success": True, "data": biometrics})
