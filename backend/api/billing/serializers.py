from rest_framework import serializers
from core.models import Invoice, Payment


class InvoiceListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_health_id = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "patient", "patient_name",
            "patient_health_id", "total_amount", "amount_paid",
            "balance", "status", "created_at", "visit", "admission",
        ]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_patient_health_id(self, obj):
        return obj.patient.health_id if obj.patient else None


class InvoiceDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_health_id = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "patient", "patient_name",
            "patient_health_id", "visit", "admission",
            "consultation_fee", "lab_fee", "pharmacy_fee",
            "admission_fee", "radiology_fee", "other_fees",
            "discount", "tax", "total_amount", "amount_paid",
            "balance", "status", "insurance_provider",
            "insurance_policy_no", "notes", "payments",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "invoice_number", "total_amount", "amount_paid",
            "balance", "status", "created_at", "updated_at",
        ]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_patient_health_id(self, obj):
        return obj.patient.health_id if obj.patient else None

    def get_payments(self, obj):
        return PaymentSerializer(obj.payments.all(), many=True).data


class InvoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "patient", "visit", "admission",
            "consultation_fee", "lab_fee", "pharmacy_fee",
            "admission_fee", "radiology_fee", "other_fees",
            "discount", "tax", "insurance_provider",
            "insurance_policy_no", "notes",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    received_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id", "invoice", "amount_paid", "payment_method",
            "transaction_reference", "payment_date",
            "received_by", "received_by_name", "notes", "created_at",
        ]
        read_only_fields = ["id", "received_by", "created_at"]

    def get_received_by_name(self, obj):
        if obj.received_by:
            return obj.received_by.get_full_name() or obj.received_by.email
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["received_by"] = request.user
        return super().create(validated_data)
