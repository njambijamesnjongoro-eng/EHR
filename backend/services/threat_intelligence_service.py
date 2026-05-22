from datetime import timedelta
from collections import defaultdict

from django.db.models import Count, Q
from django.utils import timezone

from core.models import OperationalAlert, SecurityEvent, User, LoginAttempt, EnterpriseAuditEvent
from events.event_bus import EventBus


class ThreatIntelligenceService:
    """Healthcare threat intelligence — login anomaly detection, access pattern analysis, and security alerting."""

    @staticmethod
    def analyze_login_anomalies(hours=24) -> list:
        since = timezone.now() - timedelta(hours=hours)

        login_attempts = LoginAttempt.objects.filter(
            attempted_at__gte=since,
        )

        failed_logins = login_attempts.filter(is_successful=False)

        ip_clusters = failed_logins.values("ip_address").annotate(
            count=Count("id"),
        ).filter(count__gte=5).order_by("-count")

        user_clusters = failed_logins.values("user_id").annotate(
            count=Count("id"),
        ).filter(count__gte=3).order_by("-count")

        anomalies = []
        for ip in ip_clusters:
            anomalies.append({
                "type": "brute_force",
                "severity": "critical" if ip["count"] >= 20 else "high",
                "indicator": f"IP {ip['ip_address']}",
                "failed_attempts": ip["count"],
                "detail": f"{ip['count']} failed login attempts from {ip['ip_address']} in {hours}h",
                "recommended_action": "Block IP address and investigate source",
            })

        for u in user_clusters:
            user = User.objects.filter(id=u["user_id"]).first()
            anomalies.append({
                "type": "account_compromise",
                "severity": "high",
                "indicator": f"User {user.username if user else u['user_id']}" if user else f"User {u['user_id']}",
                "failed_attempts": u["count"],
                "detail": f"{u['count']} failed login attempts for user account in {hours}h",
                "recommended_action": "Force password reset and review recent account activity",
            })

        return anomalies

    @staticmethod
    def detect_suspicious_access_patterns(days=7) -> list:
        since = timezone.now() - timedelta(days=days)

        security_events = SecurityEvent.objects.filter(
            detected_at__gte=since,
        ).filter(
            Q(severity__in=["high", "critical"]) | Q(event_type__in=[
                "unauthorized_access", "privilege_escalation", "data_exfiltration",
            ]),
        )

        by_user = security_events.values("user_id").annotate(
            count=Count("id"),
        ).filter(count__gte=3)

        suspicious = []
        for entry in by_user:
            user = User.objects.filter(id=entry["user_id"]).first()
            events = security_events.filter(user_id=entry["user_id"]).order_by("-detected_at")[:5]

            suspicious.append({
                "user_id": entry["user_id"],
                "username": user.username if user else "Unknown",
                "event_count": entry["count"],
                "severity": "critical" if entry["count"] >= 10 else "high",
                "recent_events": [
                    {"type": e.event_type, "severity": e.severity, "detected_at": e.detected_at.isoformat()}
                    for e in events
                ],
                "recommended_action": "Immediate account review and access revocation",
            })

        return suspicious

    @staticmethod
    def generate_threat_intel_report(days=30) -> dict:
        since = timezone.now() - timedelta(days=days)

        security_events = SecurityEvent.objects.filter(detected_at__gte=since)
        login_attempts = LoginAttempt.objects.filter(attempted_at__gte=since)

        total_events = security_events.count()
        critical_events = security_events.filter(severity__in=["high", "critical"]).count()
        total_logins = login_attempts.count()
        failed_logins = login_attempts.filter(is_successful=False).count()

        event_by_type = dict(security_events.values("event_type").annotate(count=Count("id")).order_by("-count"))
        event_by_severity = dict(security_events.values("severity").annotate(count=Count("id")).order_by("-count"))

        top_ip_threats = login_attempts.filter(
            is_successful=False,
        ).values("ip_address").annotate(
            count=Count("id"),
        ).order_by("-count")[:10]

        return {
            "report_period_days": days,
            "total_security_events": total_events,
            "critical_events": critical_events,
            "total_login_attempts": total_logins,
            "failed_login_rate_pct": round(failed_logins / total_logins * 100, 1) if total_logins > 0 else 0,
            "events_by_type": event_by_type,
            "events_by_severity": event_by_severity,
            "top_threat_ips": list(top_ip_threats),
            "threat_level": "critical" if critical_events > 50 else "elevated" if critical_events > 10 else "normal",
            "recommendations": [
                "Enable multi-factor authentication for all users",
                "Review and rotate API keys",
                "Conduct security awareness training",
            ],
        }

    @staticmethod
    def analyze_privilege_escalation(days=7) -> list:
        since = timezone.now() - timedelta(days=days)

        privilege_events = SecurityEvent.objects.filter(
            detected_at__gte=since,
        ).filter(
            Q(event_type__icontains="privilege") | Q(event_type__icontains="escalation"),
        )

        by_user = privilege_events.values("user_id", "event_type").annotate(
            count=Count("id"),
        ).order_by("-count")

        findings = []
        for entry in by_user:
            user = User.objects.filter(id=entry["user_id"]).first()
            if entry["count"] >= 2:
                findings.append({
                    "user_id": entry["user_id"],
                    "username": user.username if user else "Unknown",
                    "event_type": entry["event_type"],
                    "occurrences": entry["count"],
                    "severity": "critical" if entry["count"] >= 5 else "high",
                    "recommended_action": "Audit user permissions and roles immediately",
                })

        return findings

    @staticmethod
    def get_healthcare_threat_landscape() -> dict:
        total_active_threats = SecurityEvent.objects.filter(
            detected_at__gte=timezone.now() - timedelta(days=7),
            severity__in=["high", "critical"],
        ).count()

        phishing_attempts = SecurityEvent.objects.filter(
            event_type__icontains="phishing",
            detected_at__gte=timezone.now() - timedelta(days=30),
        ).count()

        ransomware_signals = SecurityEvent.objects.filter(
            event_type__icontains="ransomware",
            detected_at__gte=timezone.now() - timedelta(days=30),
        ).count()

        return {
            "active_threats_7d": total_active_threats,
            "phishing_attempts_30d": phishing_attempts,
            "ransomware_signals_30d": ransomware_signals,
            "threat_level": "critical" if total_active_threats > 20 else "elevated" if total_active_threats > 5 else "normal",
            "healthcare_specific_vectors": [
                "Ransomware targeting hospital systems",
                "Phishing targeting administrative staff",
                "Insider threats accessing patient records",
                "IoT device vulnerabilities in smart hospitals",
            ],
            "recommended_defenses": [
                "Network segmentation for medical devices",
                "Regular security training for all staff",
                "Zero-trust architecture implementation",
                "Real-time threat monitoring and SIEM integration",
            ],
        }

    @staticmethod
    def create_operational_alert_from_threat(category, severity, title, description) -> OperationalAlert:
        alert = OperationalAlert.objects.create(
            category=category,
            severity=severity,
            title=title,
            description=description,
            source_service="threat_intelligence",
        )

        EventBus.emit_security(
            event_type=f"threat_intelligence.alert.{category}.{severity}",
            data={
                "alert_id": alert.id,
                "category": category,
                "severity": severity,
                "title": title,
            },
            aggregate_type="OperationalAlert",
            aggregate_id=str(alert.id),
        )

        return alert
