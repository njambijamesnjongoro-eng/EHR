from rest_framework import serializers
from core.models import InfrastructureTwin


class InfrastructureTwinSerializer(serializers.ModelSerializer):
    hospital_name = serializers.SerializerMethodField()
    twin_type_display = serializers.CharField(source="get_twin_type_display", read_only=True)
    simulation_status_display = serializers.CharField(source="get_simulation_status_display", read_only=True)

    class Meta:
        model = InfrastructureTwin
        fields = [
            "id", "twin_type", "twin_type_display", "name", "hospital", "hospital_name",
            "region", "description", "simulation_status", "simulation_status_display",
            "current_parameters", "simulation_results", "baseline_metrics",
            "predictive_scenarios", "last_simulated_at", "metadata", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["last_simulated_at", "created_at", "updated_at"]

    def get_hospital_name(self, obj):
        return obj.hospital.hospital_name if obj.hospital else ""


class RunSimulationSerializer(serializers.Serializer):
    parameters = serializers.JSONField(default=dict)


class CreateScenarioSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=300)
    parameters = serializers.JSONField(default=dict)


class CompareScenariosSerializer(serializers.Serializer):
    scenario_ids = serializers.ListField(child=serializers.IntegerField())
