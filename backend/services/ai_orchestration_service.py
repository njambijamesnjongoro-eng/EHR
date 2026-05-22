from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import AIModelRegistry, User, EventStreamLog, EnterpriseAuditEvent, AIRecommendation
from events.event_bus import EventBus


class AIOrchestrationLayerService:
    """AI model governance and orchestration — registry, audit trails, model lifecycle management, and compliance."""

    @staticmethod
    def register_model(model_name, model_version, model_type, input_schema=None, output_schema=None, **kwargs) -> AIModelRegistry:
        model, created = AIModelRegistry.objects.update_or_create(
            model_name=model_name,
            model_version=model_version,
            defaults={
                "model_type": model_type,
                "description": kwargs.get("description", ""),
                "input_schema": input_schema or {},
                "output_schema": output_schema or {},
                "model_artifact_path": kwargs.get("artifact_path", ""),
                "explainability_config": kwargs.get("explainability_config", {}),
                "metadata": kwargs.get("metadata", {}),
                "status": AIModelRegistry.ModelStatus.DEV,
            },
        )

        EventBus.emit_ai(
            event_type="ai_model.registered" if created else "ai_model.updated",
            data={
                "model_id": model.id,
                "model_name": model_name,
                "model_version": model_version,
                "model_type": model_type,
            },
            aggregate_type="AIModelRegistry",
            aggregate_id=str(model.id),
        )

        return model

    @staticmethod
    def update_model_status(model_id, status, user) -> AIModelRegistry:
        try:
            model = AIModelRegistry.objects.get(id=model_id)
        except AIModelRegistry.DoesNotExist:
            raise ValueError(f"AI model {model_id} not found")

        previous_status = model.status
        model.status = status

        if status == AIModelRegistry.ModelStatus.PRODUCTION:
            model.governance_approval = True
            model.approved_by = user
            model.approved_at = timezone.now()

        audit_entry = {
            "timestamp": timezone.now().isoformat(),
            "user_id": user.id,
            "action": "status_change",
            "from": previous_status,
            "to": status,
        }
        model.audit_trail.append(audit_entry)
        model.save()

        EventBus.emit_ai(
            event_type=f"ai_model.status.{status}",
            data={
                "model_id": model.id,
                "model_name": model.model_name,
                "previous_status": previous_status,
                "new_status": status,
                "updated_by": user.id,
            },
            aggregate_type="AIModelRegistry",
            aggregate_id=str(model.id),
        )

        return model

    @staticmethod
    def get_model_registry(model_type=None, status=None) -> list:
        qs = AIModelRegistry.objects.filter(is_active=True)
        if model_type:
            qs = qs.filter(model_type=model_type)
        if status:
            qs = qs.filter(status=status)
        return list(qs.select_related("approved_by").order_by("-created_at"))

    @staticmethod
    def record_inference(model_id, input_data, output_data, patient_id=None, user_id=None) -> dict:
        try:
            model = AIModelRegistry.objects.get(id=model_id)
        except AIModelRegistry.DoesNotExist:
            return {"error": "AI model not found"}

        inference_id = None
        audit_entry = {
            "timestamp": timezone.now().isoformat(),
            "action": "inference",
            "input_summary": str(input_data)[:200] if input_data else "",
            "output_summary": str(output_data)[:200] if output_data else "",
            "patient_id": patient_id,
            "user_id": user_id,
        }
        model.audit_trail.append(audit_entry)
        model.save(update_fields=["audit_trail"])

        EventBus.emit_ai(
            event_type="ai_model.inference",
            data={
                "model_id": model.id,
                "model_name": model.model_name,
                "patient_id": patient_id,
                "user_id": user_id,
            },
            aggregate_type="AIModelRegistry",
            aggregate_id=str(model.id),
        )

        return {
            "model_id": model.id,
            "model_name": model.model_name,
            "inference_logged": True,
            "timestamp": audit_entry["timestamp"],
        }

    @staticmethod
    def get_model_governance_report(model_id) -> dict:
        try:
            model = AIModelRegistry.objects.select_related("approved_by").get(
                id=model_id, is_active=True,
            )
        except AIModelRegistry.DoesNotExist:
            return {"error": "AI model not found"}

        return {
            "model_id": model.id,
            "model_name": model.model_name,
            "model_version": model.model_version,
            "model_type": model.model_type,
            "status": model.status,
            "governance_approval": model.governance_approval,
            "approved_by": model.approved_by.get_full_name() if model.approved_by else None,
            "approved_at": model.approved_at.isoformat() if model.approved_at else None,
            "audit_trail_entries": len(model.audit_trail),
            "performance_metrics": model.performance_metrics,
            "explainability_config": model.explainability_config,
            "is_active": model.is_active,
        }

    @staticmethod
    def get_ai_audit_trail(model_id=None, days=30) -> list:
        since = timezone.now() - timedelta(days=days)

        if model_id:
            try:
                model = AIModelRegistry.objects.get(id=model_id)
                entries = model.audit_trail or []
                filtered = [e for e in entries if e.get("timestamp", "") >= since.isoformat()]
                return filtered
            except AIModelRegistry.DoesNotExist:
                return []

        events = EventStreamLog.objects.filter(
            event_source="ai",
            occurred_at__gte=since,
        )
        if model_id:
            events = events.filter(aggregate_id=str(model_id))
        return list(events.order_by("-occurred_at")[:100])
