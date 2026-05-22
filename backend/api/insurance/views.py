from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import InsuranceProfile, InsuranceClaim, Invoice
from core.permissions import IsStaff
from services.insurance_service import InsuranceService
from .serializers import (
    InsuranceProfileSerializer, InsuranceProfileListSerializer,
    InsuranceClaimSerializer, ClaimSubmissionSerializer,
)


class InsuranceProfileViewSet(viewsets.ModelViewSet):
    queryset = InsuranceProfile.objects.select_related("patient").all()
    permission_classes = [IsAuthenticated, IsStaff]
    filterset_fields = ["provider", "is_active", "patient"]
    search_fields = ["policy_number", "patient__first_name", "patient__last_name", "patient__health_id"]

    def get_serializer_class(self):
        if self.action == "list":
            return InsuranceProfileListSerializer
        return InsuranceProfileSerializer

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        profile = self.get_object()
        result = InsuranceService.verify_coverage(profile)
        profile.verified = result.get("verified", False)
        profile.verification_data = result
        profile.save(update_fields=["verified", "verification_data"])
        return Response({"success": True, "data": result})


class InsuranceClaimViewSet(viewsets.ModelViewSet):
    queryset = InsuranceClaim.objects.select_related(
        "insurance_profile__patient", "invoice", "submitted_by"
    ).all()
    serializer_class = InsuranceClaimSerializer
    permission_classes = [IsAuthenticated, IsStaff]
    filterset_fields = ["status", "insurance_profile"]
    ordering = ["-created_at"]

    @action(detail=False, methods=["post"])
    def submit(self, request):
        serializer = ClaimSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            profile = InsuranceProfile.objects.get(id=serializer.validated_data["insurance_profile"])
        except InsuranceProfile.DoesNotExist:
            return Response({"success": False, "message": "Insurance profile not found"}, status=status.HTTP_404_NOT_FOUND)

        invoice = None
        if serializer.validated_data.get("invoice"):
            try:
                invoice = Invoice.objects.get(id=serializer.validated_data["invoice"])
            except Invoice.DoesNotExist:
                return Response({"success": False, "message": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        claim = InsuranceService.submit_claim(
            insurance_profile=profile,
            invoice=invoice,
            submitted_by=request.user,
            claim_data=serializer.validated_data["claim_data"],
        )

        output = InsuranceClaimSerializer(claim, context={"request": request})
        return Response({"success": True, "data": output.data}, status=status.HTTP_201_CREATED)
