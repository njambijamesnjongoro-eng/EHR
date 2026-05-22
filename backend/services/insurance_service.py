from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.models import InsuranceProfile, InsuranceClaim, EnterpriseAuditEvent


class InsuranceService:
    """Insurance/SHA integration service layer."""

    @staticmethod
    def verify_coverage(insurance_profile: InsuranceProfile) -> dict:
        if insurance_profile.provider == InsuranceProfile.InsuranceProvider.SHA:
            return InsuranceService._verify_sha(insurance_profile)
        return InsuranceService._verify_private(insurance_profile)

    @staticmethod
    def _verify_sha(profile: InsuranceProfile) -> dict:
        # SHA integration placeholder — will call live API in Phase 5
        return {
            "verified": True,
            "provider": "SHA",
            "coverage_active": profile.is_active,
            "verification_source": "sha_mock",
            "message": "SHA verification endpoint — integration pending",
        }

    @staticmethod
    def _verify_private(profile: InsuranceProfile) -> dict:
        return {
            "verified": profile.verified,
            "provider": profile.provider,
            "coverage_active": profile.is_active,
            "verification_source": "manual",
        }

    @staticmethod
    @transaction.atomic
    def submit_claim(insurance_profile: InsuranceProfile, invoice, submitted_by, claim_data: dict) -> InsuranceClaim:
        claim = InsuranceClaim.objects.create(
            insurance_profile=insurance_profile,
            invoice=invoice,
            claim_number=InsuranceService._generate_claim_number(insurance_profile),
            status=InsuranceClaim.ClaimStatus.SUBMITTED,
            total_amount=invoice.total_amount if invoice else claim_data.get("total_amount", 0),
            claim_data=claim_data,
            submitted_by=submitted_by,
            submitted_at=timezone.now(),
        )

        EnterpriseAuditEvent.objects.create(
            event_type=EnterpriseAuditEvent.EventType.INTEGRATION,
            action="claim_submitted",
            resource_type="InsuranceClaim",
            resource_id=str(claim.id),
            description=f"Insurance claim {claim.claim_number} submitted for {insurance_profile.patient.health_id}",
        )

        return claim

    @staticmethod
    def _generate_claim_number(profile: InsuranceProfile) -> str:
        prefix = profile.provider.upper()
        ts = timezone.now().strftime("%y%m%d%H%M%S")
        return f"{prefix}-{ts}-{profile.patient_id}"

    @staticmethod
    def process_claim_response(claim: InsuranceClaim, response_data: dict):
        claim.response_data = response_data
        status = response_data.get("status", "pending")
        claim.status = status
        if "approved_amount" in response_data:
            claim.approved_amount = Decimal(str(response_data["approved_amount"]))
        claim.responded_at = timezone.now()
        claim.save(update_fields=["status", "approved_amount", "response_data", "responded_at"])

        EnterpriseAuditEvent.objects.create(
            event_type=EnterpriseAuditEvent.EventType.INTEGRATION,
            action="claim_response",
            resource_type="InsuranceClaim",
            resource_id=str(claim.id),
            description=f"Claim {claim.claim_number} response: {status}",
            metadata=response_data,
        )
