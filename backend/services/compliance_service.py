from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone

from core.models import ConsentLog, EnterpriseAuditEvent, SecurityEvent


class ComplianceService:
    """Healthcare compliance, consent management, and governance."""

    @staticmethod
    def record_consent(patient, consent_type, granted_by, consent_version="1.0", metadata=None, expires_days=None) -> ConsentLog:
        consent = ConsentLog.objects.create(
            patient=patient,
            consent_type=consent_type,
            status=ConsentLog.ConsentStatus.GRANTED,
            granted_by=granted_by,
            consent_version=consent_version,
            metadata=metadata or {},
            expires_at=timezone.now() + timedelta(days=expires_days) if expires_days else None,
        )

        EnterpriseAuditEvent.objects.create(
            event_type=EnterpriseAuditEvent.EventType.ADMIN,
            action="consent_granted",
            resource_type="ConsentLog",
            resource_id=str(consent.id),
            description=f"Consent {consent_type} granted for {patient.health_id}",
        )

        return consent

    @staticmethod
    @transaction.atomic
    def revoke_consent(consent: ConsentLog, revoked_by, reason: str = ""):
        consent.status = ConsentLog.ConsentStatus.REVOKED
        consent.revoked_at = timezone.now()
        consent.revocation_reason = reason
        consent.save()

        EnterpriseAuditEvent.objects.create(
            event_type=EnterpriseAuditEvent.EventType.ADMIN,
            action="consent_revoked",
            resource_type="ConsentLog",
            resource_id=str(consent.id),
            description=f"Consent {consent.consent_type} revoked for {consent.patient.health_id}: {reason}",
        )

    @staticmethod
    def check_consent(patient, consent_type) -> bool:
        return ConsentLog.objects.filter(
            patient=patient,
            consent_type=consent_type,
            status=ConsentLog.ConsentStatus.GRANTED,
            expires_at__isnull=True,
        ).exists() or ConsentLog.objects.filter(
            patient=patient,
            consent_type=consent_type,
            status=ConsentLog.ConsentStatus.GRANTED,
            expires_at__gte=timezone.now(),
        ).exists()

    @staticmethod
    def get_active_consents(patient):
        return ConsentLog.objects.filter(
            patient=patient,
            status=ConsentLog.ConsentStatus.GRANTED,
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=timezone.now()),
        )

    @staticmethod
    def expire_consents():
        expired = ConsentLog.objects.filter(
            status=ConsentLog.ConsentStatus.GRANTED,
            expires_at__lt=timezone.now(),
        )
        count = expired.count()
        expired.update(status=ConsentLog.ConsentStatus.EXPIRED)
        return count

    @staticmethod
    def generate_audit_report(days: int = 30) -> dict:
        since = timezone.now() - timedelta(days=days)
        events = EnterpriseAuditEvent.objects.filter(created_at__gte=since)

        return {
            "period_days": days,
            "total_events": events.count(),
            "by_event_type": dict(events.values_list("event_type").annotate(c=Count("id")).order_by("-c")),
            "by_severity": dict(events.values_list("severity").annotate(c=Count("id")).order_by("-c")),
            "by_user": dict(
                events.values_list("user__email")
                .annotate(c=Count("id"))
                .order_by("-c")[:10]
            ),
            "security_events": SecurityEvent.objects.filter(
                detected_at__gte=since,
                severity__in=["high", "critical"],
            ).count(),
        }



