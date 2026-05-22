import json
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from core.models import ExternalSystem, EnterpriseAuditEvent


class InteroperabilityService:
    """External system integration and FHIR compatibility layer."""

    @staticmethod
    def register_external_system(name, system_type, base_url, hospital=None, auth_type="api_key", config=None) -> ExternalSystem:
        system, created = ExternalSystem.objects.update_or_create(
            system_name=name,
            defaults={
                "system_type": system_type,
                "hospital": hospital,
                "base_url": base_url,
                "auth_type": auth_type,
                "config": config or {},
            },
        )

        EnterpriseAuditEvent.objects.create(
            event_type=EnterpriseAuditEvent.EventType.INTEGRATION,
            action="system_registered",
            resource_type="ExternalSystem",
            resource_id=str(system.id),
            description=f"External system {name} ({system_type}) registered",
        )

        return system

    @staticmethod
    def convert_to_fhir(resource_type: str, data: dict) -> dict:
        """Convert internal data structure to FHIR-compatible format.

        FHIR R4 compatibility layer — foundation for future full FHIR server.
        """
        fhir_mapping = {
            "Patient": InteroperabilityService._patient_to_fhir,
            "Encounter": InteroperabilityService._encounter_to_fhir,
            "Observation": InteroperabilityService._observation_to_fhir,
            "MedicationRequest": InteroperabilityService._medication_to_fhir,
            "DiagnosticReport": InteroperabilityService._lab_to_fhir,
        }

        converter = fhir_mapping.get(resource_type)
        if converter:
            return converter(data)
        return {"resourceType": resource_type, "data": data}

    @staticmethod
    def _patient_to_fhir(data: dict) -> dict:
        return {
            "resourceType": "Patient",
            "id": str(data.get("id", "")),
            "identifier": [
                {"system": "http://example.org/health-id", "value": data.get("health_id", "")},
            ],
            "name": [{"family": data.get("last_name", ""), "given": [data.get("first_name", "")]}],
            "gender": data.get("gender", "unknown"),
            "birthDate": str(data.get("date_of_birth", "")),
            "telecom": [
                {"system": "phone", "value": data.get("phone_number", "")},
            ],
        }

    @staticmethod
    def _encounter_to_fhir(data: dict) -> dict:
        return {
            "resourceType": "Encounter",
            "id": str(data.get("id", "")),
            "status": data.get("status", "unknown"),
            "class": {"code": "AMB", "display": "ambulatory"},
            "subject": {"reference": f"Patient/{data.get('patient_id', '')}"},
            "period": {
                "start": str(data.get("visit_date", "")),
            },
        }

    @staticmethod
    def _observation_to_fhir(data: dict) -> dict:
        return {
            "resourceType": "Observation",
            "id": str(data.get("id", "")),
            "status": "final",
            "code": {"text": data.get("observation_type", "")},
            "subject": {"reference": f"Patient/{data.get('patient_id', '')}"},
            "valueQuantity": {
                "value": data.get("value"),
                "unit": data.get("unit", ""),
            },
        }

    @staticmethod
    def _medication_to_fhir(data: dict) -> dict:
        return {
            "resourceType": "MedicationRequest",
            "id": str(data.get("id", "")),
            "status": "active",
            "medicationCodeableConcept": {"text": data.get("medication_name", "")},
            "subject": {"reference": f"Patient/{data.get('patient_id', '')}"},
            "dosageInstruction": [{
                "text": f"{data.get('dosage', '')} {data.get('frequency', '')}",
            }],
        }

    @staticmethod
    def _lab_to_fhir(data: dict) -> dict:
        return {
            "resourceType": "DiagnosticReport",
            "id": str(data.get("id", "")),
            "status": "final",
            "code": {"text": data.get("test_name", "")},
            "subject": {"reference": f"Patient/{data.get('patient_id', '')}"},
            "result": [
                {"display": data.get("result_text", "")},
            ],
        }

    @staticmethod
    def convert_from_fhir(fhir_resource: dict) -> dict:
        """Convert FHIR resource back to internal format."""
        resource_type = fhir_resource.get("resourceType", "")
        if resource_type == "Patient":
            name = (fhir_resource.get("name") or [{}])[0]
            return {
                "first_name": (name.get("given") or [""])[0],
                "last_name": name.get("family", ""),
                "gender": fhir_resource.get("gender", ""),
                "date_of_birth": fhir_resource.get("birthDate", ""),
                "phone_number": next(
                    (t.get("value", "") for t in fhir_resource.get("telecom", []) if t.get("system") == "phone"),
                    "",
                ),
            }
        return fhir_resource
