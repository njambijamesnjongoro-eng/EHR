from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import InfrastructureTwin, Hospital
from events.event_bus import EventBus


class DigitalTwinService:
    """Digital twin simulation engine — operational modeling, scenario planning, and predictive simulation."""

    @staticmethod
    def create_twin(twin_type, name, hospital=None, region="", description="", parameters=None) -> InfrastructureTwin:
        twin = InfrastructureTwin.objects.create(
            twin_type=twin_type,
            name=name,
            hospital=hospital,
            region=region,
            description=description,
            current_parameters=parameters or {},
        )

        EventBus.emit(
            event_source="system",
            event_type=f"digital_twin.created.{twin_type}",
            data={
                "twin_id": twin.id,
                "twin_type": twin_type,
                "name": name,
                "hospital_id": hospital.id if hospital else None,
                "region": region,
            },
            aggregate_type="InfrastructureTwin",
            aggregate_id=str(twin.id),
        )

        return twin

    @staticmethod
    def run_simulation(twin_id) -> dict:
        try:
            twin = InfrastructureTwin.objects.get(id=twin_id, is_active=True)
        except InfrastructureTwin.DoesNotExist:
            return {"error": "Digital twin not found"}

        twin.simulation_status = InfrastructureTwin.SimulationStatus.RUNNING
        twin.save(update_fields=["simulation_status"])

        from django.db.models import Avg, Count
        from core.models import Ward, Bed, Admission, OperationalAlert

        projected_metrics = {}

        if twin.twin_type in ("hospital", "regional"):
            beds_total = Bed.objects.filter(ward__hospital_id=twin.hospital_id).count() if twin.hospital else 0
            beds_occupied = Bed.objects.filter(
                ward__hospital_id=twin.hospital_id, occupancy_status=Bed.Status.OCCUPIED,
            ).count() if twin.hospital else 0
            avg_los = Admission.objects.filter(
                patient__hospital_id=twin.hospital_id,
            ).aggregate(avg=Avg("length_of_stay_days"))["avg"] or 0
            recent_alerts = OperationalAlert.objects.filter(
                hospital_id=twin.hospital_id,
                created_at__gte=timezone.now() - timedelta(days=7),
            ).count() if twin.hospital else 0

            projected_metrics = {
                "utilization_rate": round(beds_occupied / beds_total * 100, 1) if beds_total > 0 else 0,
                "avg_length_of_stay": round(float(avg_los), 1),
                "recent_alerts": recent_alerts,
                "projected_demand_increase": round(recent_alerts * 0.05, 2),
                "efficiency_score": round(max(0, 100 - (recent_alerts * 2)), 1),
            }

        twin.simulation_results = projected_metrics
        twin.simulation_status = InfrastructureTwin.SimulationStatus.COMPLETED
        twin.last_simulated_at = timezone.now()
        twin.save(update_fields=["simulation_results", "simulation_status", "last_simulated_at"])

        EventBus.emit(
            event_source="system",
            event_type="digital_twin.simulation_completed",
            data={
                "twin_id": twin.id,
                "twin_type": twin.twin_type,
                "metrics": projected_metrics,
            },
            aggregate_type="InfrastructureTwin",
            aggregate_id=str(twin.id),
        )

        return {
            "twin_id": twin.id,
            "twin_name": twin.name,
            "status": twin.simulation_status,
            "simulated_at": twin.last_simulated_at.isoformat(),
            "results": projected_metrics,
        }

    @staticmethod
    def get_twin_status(twin_id) -> dict:
        try:
            twin = InfrastructureTwin.objects.select_related("hospital").get(id=twin_id)
        except InfrastructureTwin.DoesNotExist:
            return {"error": "Digital twin not found"}

        return {
            "twin_id": twin.id,
            "name": twin.name,
            "twin_type": twin.twin_type,
            "hospital": twin.hospital.name if twin.hospital else None,
            "region": twin.region,
            "description": twin.description,
            "simulation_status": twin.simulation_status,
            "last_simulated_at": twin.last_simulated_at.isoformat() if twin.last_simulated_at else None,
            "scenario_count": len(twin.predictive_scenarios),
            "is_active": twin.is_active,
            "created_at": twin.created_at.isoformat(),
        }

    @staticmethod
    def list_twins(twin_type=None, hospital_id=None, region=None) -> list:
        qs = InfrastructureTwin.objects.select_related("hospital").filter(is_active=True)
        if twin_type:
            qs = qs.filter(twin_type=twin_type)
        if hospital_id:
            qs = qs.filter(hospital_id=hospital_id)
        if region:
            qs = qs.filter(region=region)
        return list(qs.order_by("-created_at"))

    @staticmethod
    def create_emergency_scenario(twin_id, scenario_params) -> dict:
        try:
            twin = InfrastructureTwin.objects.get(id=twin_id, is_active=True)
        except InfrastructureTwin.DoesNotExist:
            return {"error": "Digital twin not found"}

        scenario = {
            "id": len(twin.predictive_scenarios) + 1,
            "created_at": timezone.now().isoformat(),
            "parameters": scenario_params,
        }
        twin.predictive_scenarios.append(scenario)
        twin.save(update_fields=["predictive_scenarios"])

        EventBus.emit(
            event_source="system",
            event_type="digital_twin.scenario_created",
            data={
                "twin_id": twin.id,
                "scenario_id": scenario["id"],
                "scenario_params": scenario_params,
            },
            aggregate_type="InfrastructureTwin",
            aggregate_id=str(twin.id),
        )

        return {
            "twin_id": twin.id,
            "scenario_id": scenario["id"],
            "total_scenarios": len(twin.predictive_scenarios),
        }

    @staticmethod
    def compare_scenarios(twin_id) -> dict:
        try:
            twin = InfrastructureTwin.objects.get(id=twin_id, is_active=True)
        except InfrastructureTwin.DoesNotExist:
            return {"error": "Digital twin not found"}

        scenarios = twin.predictive_scenarios
        if not scenarios:
            return {"twin_id": twin.id, "scenario_count": 0, "message": "No scenarios to compare"}

        comparisons = []
        for s in scenarios:
            params = s.get("parameters", {})
            comparisons.append({
                "scenario_id": s.get("id"),
                "created_at": s.get("created_at"),
                "impact_level": params.get("impact_level", "unknown"),
                "resource_requirement": params.get("resource_requirement", "unknown"),
                "estimated_recovery_hours": params.get("estimated_recovery_hours"),
                "affected_assets": params.get("affected_assets", []),
            })

        return {
            "twin_id": twin.id,
            "twin_name": twin.name,
            "scenario_count": len(scenarios),
            "scenarios": comparisons,
            "recommendation": "Scenario with lowest recovery time and resource requirement is optimal",
        }
