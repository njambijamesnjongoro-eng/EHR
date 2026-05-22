import hashlib
import json
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import BiometricIdentity, SecurityEvent, EnterpriseAuditEvent
from events.event_bus import EventBus


class BiometricService:
    """Biometric authentication framework.

    Stores only encrypted templates and hashed identifiers.
    Never stores raw biometric data.
    """

    @staticmethod
    def register_biometric(user, biometric_type: str, encrypted_template: str, device_id: str = "") -> BiometricIdentity:
        biometric_hash = hashlib.sha256(
            f"{user.id}:{biometric_type}:{timezone.now().isoformat()}".encode()
        ).hexdigest()

        BiometricIdentity.objects.filter(user=user, biometric_type=biometric_type, is_active=True).update(is_active=False)

        identity = BiometricIdentity.objects.create(
            user=user,
            biometric_type=biometric_type,
            biometric_hash=biometric_hash,
            encrypted_template=encrypted_template,
            device_id=device_id,
        )

        EventBus.emit_security(
            event_type="biometric.registered",
            data={
                "identity_id": identity.id,
                "user_id": user.id,
                "biometric_type": biometric_type,
            },
            aggregate_type="BiometricIdentity",
            aggregate_id=str(identity.id),
        )

        return identity

    @staticmethod
    def verify_biometric(user, biometric_type: str, encrypted_template: str) -> bool:
        try:
            identity = BiometricIdentity.objects.get(
                user=user,
                biometric_type=biometric_type,
                is_active=True,
            )
        except BiometricIdentity.DoesNotExist:
            return False

        if identity.encrypted_template == encrypted_template:
            identity.fail_count = 0
            identity.verified_at = timezone.now()
            identity.save(update_fields=["fail_count", "verified_at"])

            EventBus.emit_security(
                event_type="biometric.verified",
                data={
                    "identity_id": identity.id,
                    "user_id": user.id,
                    "biometric_type": biometric_type,
                },
                aggregate_type="BiometricIdentity",
                aggregate_id=str(identity.id),
            )
            return True
        else:
            identity.fail_count += 1
            identity.save(update_fields=["fail_count"])

            if identity.fail_count >= 5:
                identity.is_active = False
                identity.save(update_fields=["is_active"])

                SecurityEvent.objects.create(
                    category=SecurityEvent.EventCategory.AUTH_FAILURE,
                    severity=SecurityEvent.Severity.MEDIUM,
                    user=user,
                    description=f"Biometric locked after {identity.fail_count} failed attempts ({biometric_type})",
                    metadata={"biometric_type": biometric_type, "fail_count": identity.fail_count},
                )

            return False

    @staticmethod
    def deactivate_biometric(identity_id: int) -> bool:
        try:
            identity = BiometricIdentity.objects.get(id=identity_id)
        except BiometricIdentity.DoesNotExist:
            return False

        identity.is_active = False
        identity.save(update_fields=["is_active"])

        EventBus.emit_security(
            event_type="biometric.deactivated",
            data={
                "identity_id": identity.id,
                "user_id": identity.user_id,
                "biometric_type": identity.biometric_type,
            },
            aggregate_type="BiometricIdentity",
            aggregate_id=str(identity.id),
        )

        return True

    @staticmethod
    def get_user_biometrics(user) -> list:
        return list(BiometricIdentity.objects.filter(user=user).values(
            "id", "biometric_type", "is_active", "verified_at", "fail_count", "created_at",
        ))

    @staticmethod
    def is_biometric_active(user, biometric_type: str) -> bool:
        return BiometricIdentity.objects.filter(
            user=user,
            biometric_type=biometric_type,
            is_active=True,
        ).exists()
