from datetime import timedelta
from collections import defaultdict

from django.db.models import Count, Avg, Q
from django.utils import timezone

from core.models import (
    SecurityEvent, EnterpriseAuditEvent, DeviceFingerprint,
    User, EventStreamLog,
)
from events.event_bus import EventBus


class AdvancedSecurityService:
    """Advanced threat detection, behavioral analytics, and AI-assisted security."""

    @staticmethod
    def analyze_behavioral_anomaly(user, days: int = 7) -> dict:
        since = timezone.now() - timedelta(days=days)

        user_events = SecurityEvent.objects.filter(
            user=user, detected_at__gte=since,
        ).order_by("-detected_at")

        audit_events = EnterpriseAuditEvent.objects.filter(
            user=user, created_at__gte=since,
        ).order_by("-created_at")

        unusual_times = audit_events.filter(
            Q(created_at__hour__gte=22) | Q(created_at__hour__lte=5),
        ).count()

        high_risk_events = user_events.filter(risk_score__gte=0.7).count()

        devices = DeviceFingerprint.objects.filter(user=user)
        recent_ip_count = devices.values("ip_address").distinct().count()

        anomaly_score = 0.0
        findings = []

        if unusual_times > 10:
            anomaly_score += 0.2
            findings.append(f"{unusual_times} actions outside business hours")

        if high_risk_events > 3:
            anomaly_score += 0.3
            findings.append(f"{high_risk_events} high-risk security events")

        if recent_ip_count > 5:
            anomaly_score += 0.2
            findings.append(f"Access from {recent_ip_count} different IPs")

        return {
            "user_id": user.id,
            "user_email": user.email,
            "period_days": days,
            "anomaly_score": round(anomaly_score, 2),
            "findings": findings,
            "unusual_hour_actions": unusual_times,
            "high_risk_events": high_risk_events,
            "distinct_ips": recent_ip_count,
        }

    @staticmethod
    def detect_privilege_abuse(days: int = 7) -> list:
        since = timezone.now() - timedelta(days=days)

        admin_actions = EnterpriseAuditEvent.objects.filter(
            event_type__in=["admin", "security"],
            created_at__gte=since,
        ).values("user__email", "action").annotate(
            count=Count("id"),
        ).order_by("-count")[:50]

        sensitive_resources = EnterpriseAuditEvent.objects.filter(
            resource_type__in=["Patient", "User", "ConsentLog", "SecurityEvent"],
            created_at__gte=since,
        ).values("user__email", "action", "resource_type").annotate(
            count=Count("id"),
        ).order_by("-count")[:50]

        return {
            "admin_actions": list(admin_actions),
            "sensitive_access": list(sensitive_resources),
        }

    @staticmethod
    def threat_hunting(days: int = 7) -> dict:
        since = timezone.now() - timedelta(days=days)

        brute_force = SecurityEvent.objects.filter(
            category=SecurityEvent.EventCategory.AUTH_FAILURE,
            detected_at__gte=since,
        ).values("ip_address").annotate(
            count=Count("id"),
            users=Count("user", distinct=True),
        ).filter(count__gte=10).order_by("-count")

        high_risk_sessions = SecurityEvent.objects.filter(
            risk_score__gte=0.8,
            detected_at__gte=since,
        ).select_related("user")

        policy_violations = SecurityEvent.objects.filter(
            category=SecurityEvent.EventCategory.POLICY_VIOLATION,
            detected_at__gte=since,
        ).select_related("user")

        return {
            "potential_brute_force": [
                {"ip": b["ip_address"], "attempts": b["count"], "targeted_users": b["users"]}
                for b in brute_force[:20]
            ],
            "high_risk_sessions": [
                {
                    "id": e.id,
                    "user": e.user.email if e.user else "Anonymous",
                    "score": e.risk_score,
                    "description": e.description,
                    "ip": e.ip_address,
                    "time": e.detected_at.isoformat(),
                }
                for e in high_risk_sessions[:20]
            ],
            "policy_violations": [
                {
                    "id": e.id,
                    "user": e.user.email if e.user else "Anonymous",
                    "description": e.description,
                    "severity": e.severity,
                    "time": e.detected_at.isoformat(),
                }
                for e in policy_violations[:20]
            ],
        }

    @staticmethod
    def correlated_event_analysis(correlation_id: str) -> dict:
        events = EventStreamLog.objects.filter(correlation_id=correlation_id).order_by("occurred_at")

        return {
            "correlation_id": correlation_id,
            "event_count": events.count(),
            "time_span": {
                "start": events.first().occurred_at.isoformat() if events.exists() else None,
                "end": events.last().occurred_at.isoformat() if events.exists() else None,
            },
            "events": [
                {
                    "source": e.event_source,
                    "type": e.event_type,
                    "time": e.occurred_at.isoformat(),
                    "summary": str(e.data)[:200],
                }
                for e in events
            ],
        }

    @staticmethod
    def distributed_audit_analysis(days: int = 30) -> dict:
        since = timezone.now() - timedelta(days=days)

        event_type_dist = EnterpriseAuditEvent.objects.filter(
            created_at__gte=since,
        ).values("event_type").annotate(
            count=Count("id"),
        ).order_by("-count")

        severity_dist = EnterpriseAuditEvent.objects.filter(
            created_at__gte=since,
        ).values("severity").annotate(
            count=Count("id"),
        ).order_by("-count")

        hourly_activity = EnterpriseAuditEvent.objects.filter(
            created_at__gte=since,
        ).extra({"hour": "extract(hour from created_at)"}).values("hour").annotate(
            count=Count("id"),
        ).order_by("hour")

        return {
            "period_days": days,
            "total_events": EnterpriseAuditEvent.objects.filter(created_at__gte=since).count(),
            "by_event_type": {e["event_type"]: e["count"] for e in event_type_dist},
            "by_severity": {e["severity"]: e["count"] for e in severity_dist},
            "hourly_activity": {int(h["hour"]): h["count"] for h in hourly_activity},
            "peak_hour": max(hourly_activity, key=lambda x: x["count"])["hour"] if hourly_activity else None,
        }
