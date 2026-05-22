import hashlib
import hmac
import time
from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from core.models import SecurityEvent, DeviceFingerprint, MFAToken, EnterpriseAuditEvent


class SecurityService:
    """Enterprise security: MFA, device fingerprinting, risk scoring, intrusion detection."""

    @staticmethod
    def generate_device_fingerprint(request) -> str:
        parts = [
            request.META.get("HTTP_USER_AGENT", ""),
            request.META.get("HTTP_ACCEPT_LANGUAGE", ""),
            request.META.get("HTTP_ACCEPT_ENCODING", ""),
            str(request.META.get("REMOTE_ADDR", "")),
        ]
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def register_device(user, request, device_name="") -> DeviceFingerprint:
        fp_hash = SecurityService.generate_device_fingerprint(request)
        device, created = DeviceFingerprint.objects.get_or_create(
            user=user,
            fingerprint_hash=fp_hash,
            defaults={
                "device_name": device_name or request.META.get("HTTP_USER_AGENT", "")[:255],
                "ip_address": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            },
        )
        if not created:
            device.save()  # updates last_seen_at
        return device

    @staticmethod
    def calculate_login_risk(user, request) -> dict:
        risk_score = 0.0
        reasons = []

        fp_hash = SecurityService.generate_device_fingerprint(request)
        is_known_device = DeviceFingerprint.objects.filter(
            user=user, fingerprint_hash=fp_hash
        ).exists()

        if not is_known_device:
            risk_score += 0.3
            reasons.append("Unknown device")

        recent_failures = SecurityEvent.objects.filter(
            user=user,
            category=SecurityEvent.EventCategory.AUTH_FAILURE,
            detected_at__gte=timezone.now() - timedelta(minutes=15),
        ).count()

        if recent_failures > 3:
            risk_score += 0.3
            reasons.append(f"{recent_failures} recent auth failures")

        if recent_failures > 10:
            risk_score += 0.4
            reasons.append("Brute force pattern detected")

        geo_mismatch = False  # Future: GeoIP check
        if geo_mismatch:
            risk_score += 0.2
            reasons.append("Geographic anomaly")

        if risk_score >= 0.7:
            SecurityEvent.objects.create(
                category=SecurityEvent.EventCategory.SUSPICIOUS_ACTIVITY,
                severity=SecurityEvent.Severity.HIGH,
                user=user,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                risk_score=risk_score,
                description="High-risk login attempt: " + "; ".join(reasons),
                metadata={"reasons": reasons, "fingerprint": fp_hash},
            )

        return {"risk_score": round(risk_score, 2), "reasons": reasons, "is_known_device": is_known_device}

    @staticmethod
    @transaction.atomic
    def log_login_attempt(user, request, success: bool):
        fp_hash = SecurityService.generate_device_fingerprint(request)

        event = SecurityEvent.objects.create(
            category=SecurityEvent.EventCategory.LOGIN_ATTEMPT,
            severity=SecurityEvent.Severity.INFO,
            user=user,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            device_fingerprint=fp_hash,
            description=f"{'Successful' if success else 'Failed'} login from {request.META.get('REMOTE_ADDR', 'unknown')}",
            metadata={"success": success},
        )

        if not success:
            risk = SecurityService.calculate_login_risk(user, request)
            if risk["risk_score"] >= 0.5:
                event.severity = SecurityEvent.Severity.MEDIUM
                event.risk_score = risk["risk_score"]
                event.save(update_fields=["severity", "risk_score"])

        return event

    @staticmethod
    def log_security_event(category, severity, description, user=None, request=None, metadata=None):
        return SecurityEvent.objects.create(
            category=category,
            severity=severity,
            user=user,
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
            description=description,
            metadata=metadata or {},
        )

    @staticmethod
    def setup_mfa(user, token_type=MFAToken.TokenType.TOTP) -> MFAToken:
        import secrets
        secret = secrets.token_hex(32)
        token = MFAToken.objects.create(
            user=user,
            token_type=token_type,
            secret=secret,
        )
        return token

    @staticmethod
    def verify_mfa(user, token_code: str) -> bool:
        # TOTP verification placeholder — integrate with authenticator apps
        tokens = MFAToken.objects.filter(user=user, is_active=True)
        for token in tokens:
            if token.token_type == MFAToken.TokenType.BACKUP:
                if token.secret == token_code:
                    token.is_active = False
                    token.save(update_fields=["is_active"])
                    return True
            elif token.token_type == MFAToken.TokenType.TOTP:
                # Future: real TOTP validation with pyotp
                pass
        return False


class SessionSecurityService:
    """Session anomaly detection and management."""

    @staticmethod
    def validate_session(user, request) -> dict:
        fp_hash = SecurityService.generate_device_fingerprint(request)
        known_device = DeviceFingerprint.objects.filter(
            user=user, fingerprint_hash=fp_hash
        ).first()

        if not known_device:
            return {"valid": False, "reason": "Unknown device"}

        if known_device.risk_count > 5:
            return {"valid": False, "reason": "High-risk device"}

        return {"valid": True}

    @staticmethod
    def flag_anomaly(user, request, reason: str):
        SecurityEvent.objects.create(
            category=SecurityEvent.EventCategory.ANOMALY,
            severity=SecurityEvent.Severity.MEDIUM,
            user=user,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            description=reason,
        )

        # Increase device risk count
        fp_hash = SecurityService.generate_device_fingerprint(request)
        DeviceFingerprint.objects.filter(
            user=user, fingerprint_hash=fp_hash
        ).update(risk_count=models.F("risk_count") + 1)



