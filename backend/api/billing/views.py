from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.models import Invoice, Payment, AuditLog
from core.permissions import IsStaff
from .serializers import (
    InvoiceListSerializer, InvoiceDetailSerializer,
    InvoiceCreateSerializer, PaymentSerializer,
)


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related("patient").all()
    filterset_fields = ["status", "patient"]
    search_fields = [
        "invoice_number", "patient__first_name",
        "patient__last_name", "patient__health_id",
    ]
    ordering_fields = ["created_at", "total_amount", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return InvoiceListSerializer
        if self.action == "create":
            return InvoiceCreateSerializer
        return InvoiceDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated(), IsStaff()]

    def perform_create(self, serializer):
        invoice = serializer.save()
        AuditLog.objects.create(
            user=self.request.user, action=AuditLog.Action.CREATE,
            resource_type="invoice", resource_id=invoice.invoice_number,
            description=f"Created invoice {invoice.invoice_number} for patient {invoice.patient.health_id}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/billing/invoices/",
        )

    @action(detail=True, methods=["get"])
    def payments(self, request, pk=None):
        invoice = self.get_object()
        payments = invoice.payments.all()
        serializer = PaymentSerializer(payments, many=True)
        return Response({"success": True, "data": serializer.data})


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("invoice", "received_by").all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsStaff]
    ordering = ["-payment_date"]

    def perform_create(self, serializer):
        payment = serializer.save()
        AuditLog.objects.create(
            user=self.request.user, action=AuditLog.Action.CREATE,
            resource_type="payment", resource_id=str(payment.id),
            description=f"Payment {payment.amount_paid} for invoice {payment.invoice.invoice_number}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            request_path="/api/billing/payments/",
        )
