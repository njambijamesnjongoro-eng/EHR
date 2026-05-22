from core.models import Notification, EnterpriseAuditEvent


class NotificationService:
    """Cross-hospital notification dispatch."""

    @staticmethod
    def send(user, title, message, category="general", patient=None, link=""):
        return Notification.objects.create(
            recipient=user,
            patient=patient,
            category=category,
            title=title,
            message=message,
            link=link,
        )

    @staticmethod
    def send_hospital_staff(hospital, title, message, category="general", patient=None, link="", roles=None):
        from core.models import HospitalStaff, User
        staff_qs = HospitalStaff.objects.filter(hospital=hospital, is_active=True)
        if roles:
            staff_qs = staff_qs.filter(staff_role__in=roles)

        user_ids = staff_qs.values_list("user_id", flat=True)
        notifications = [
            Notification(
                recipient_id=uid, patient=patient,
                category=category, title=title,
                message=message, link=link,
            )
            for uid in user_ids
        ]
        Notification.objects.bulk_create(notifications)
        return len(notifications)

    @staticmethod
    def send_referral_notification(referral):
        from core.models import HospitalStaff

        staff = HospitalStaff.objects.filter(
            hospital=referral.receiving_hospital,
            staff_role__in=["doctor", "hospital_admin"],
        ).select_related("user")

        for member in staff:
            NotificationService.send(
                user=member.user,
                title=f"New Referral: {referral.patient.full_name}",
                message=f"{referral.referring_hospital.hospital_name} referred {referral.patient.full_name} - {referral.reason_for_referral[:200]}",
                category="general",
                patient=referral.patient,
                link=f"/referrals/{referral.id}",
            )

        EnterpriseAuditEvent.objects.create(
            event_type=EnterpriseAuditEvent.EventType.INTEGRATION,
            action="referral_notification",
            resource_type="Referral",
            resource_id=str(referral.id),
            description=f"Notified {staff.count()} staff at {referral.receiving_hospital.hospital_name}",
        )
