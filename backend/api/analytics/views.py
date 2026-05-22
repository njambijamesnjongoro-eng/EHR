from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsHospitalAdmin, IsSuperAdmin
from services.analytics_service import AnalyticsService
from services.precision_health_service import PrecisionHealthService
from services.operational_intelligence_service import OperationalIntelligenceService


class HospitalDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        hospital_id = request.user.hospital_id

        data = AnalyticsService.hospital_dashboard(hospital_id, days)
        return Response({"success": True, "data": data})


class DiseaseTrendsView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 365))
        data = AnalyticsService.disease_trends(days)
        return Response({"success": True, "data": data})


class RevenueAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        months = int(request.query_params.get("months", 12))
        data = AnalyticsService.revenue_analysis(request.user.hospital_id, months)
        return Response({"success": True, "data": data})


class DepartmentUtilizationView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.user.hospital_id
        if not hospital_id:
            return Response({"success": False, "message": "No hospital affiliation"}, status=400)

        from core.models import Hospital
        hospital = Hospital.objects.get(id=hospital_id)
        data = AnalyticsService.department_utilization(hospital)
        return Response({"success": True, "data": data})


class NationalAggregateView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        data = AnalyticsService.national_aggregate()
        return Response({"success": True, "data": data})


class PredictiveHospitalLoadView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        from services.predictive_service import PredictiveAnalyticsService
        hospital_id = request.user.hospital_id
        days = int(request.query_params.get("days_ahead", 7))
        data = PredictiveAnalyticsService.predict_hospital_load(hospital_id, days)
        return Response({"success": True, "data": data})


class PredictivePatientFlowView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        from services.predictive_service import PredictiveAnalyticsService
        hospital_id = request.user.hospital_id
        days = int(request.query_params.get("days_ahead", 30))
        data = PredictiveAnalyticsService.predict_patient_flow(hospital_id, days)
        return Response({"success": True, "data": data})


class PredictiveAlertsView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        from services.predictive_service import PredictiveAnalyticsService
        hospital_id = request.user.hospital_id
        category = request.query_params.get("category")
        alerts = PredictiveAnalyticsService.active_alerts(hospital_id, category)

        from core.models import PredictiveAlert
        return Response({
            "success": True,
            "data": [
                {
                    "id": a.id,
                    "category": a.category,
                    "severity": a.severity,
                    "title": a.title,
                    "description": a.description,
                    "confidence_score": a.confidence_score,
                    "predicted_at": a.predicted_at.isoformat(),
                    "status": a.status,
                }
                for a in alerts
            ],
        })


class SystemAnomaliesView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        from services.predictive_service import PredictiveAnalyticsService
        alerts = PredictiveAnalyticsService.detect_system_anomalies()
        return Response({
            "success": True,
            "data": [{"id": a.id, "title": a.title, "description": a.description, "severity": a.severity} for a in alerts],
        })


class RiskProfilingTrendsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        category = request.query_params.get("category")
        days = int(request.query_params.get("days", 90))
        if not category:
            return Response({"success": False, "message": "category required"}, status=400)
        data = PrecisionHealthService.get_risk_trends(category, days)
        return Response({"success": True, "data": data})


class HighRiskPopulationView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        category = request.query_params.get("category")
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        limit = int(request.query_params.get("limit", 50))
        profiles = PrecisionHealthService.get_high_risk_patients(category, hospital_id, limit)
        return Response({
            "success": True,
            "data": [
                {
                    "patient_id": p.patient_id,
                    "patient_name": p.patient.full_name if p.patient else "",
                    "risk_category": p.risk_category,
                    "risk_score": p.risk_score,
                    "risk_level": p.risk_level,
                    "last_assessed": p.last_assessed_at.isoformat(),
                }
                for p in profiles
            ],
        })


# ─── Phase 8 Extensions ───
class HospitalEfficiencyView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        data = OperationalIntelligenceService.get_hospital_efficiency(hospital_id)
        return Response({"success": True, "data": data})


class ResourceAllocationView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        data = OperationalIntelligenceService.get_resource_allocation(hospital_id)
        return Response({"success": True, "data": data})


class OperationalBottlenecksView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        data = OperationalIntelligenceService.get_operational_bottlenecks(hospital_id)
        return Response({"success": True, "data": data})


class OptimizationRecommendationsView(APIView):
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    def get(self, request):
        hospital_id = request.query_params.get("hospital_id") or request.user.hospital_id
        data = OperationalIntelligenceService.get_optimization_recommendations(hospital_id)
        return Response({"success": True, "data": data})
