import uuid
import hashlib
import json
from datetime import date
from decimal import Decimal

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.utils import timezone


# ─── Custom User Manager ───
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)
        return self.create_user(email, password, **extra_fields)


# ─── User Model ───
class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"
        DOCTOR = "doctor", "Doctor"
        NURSE = "nurse", "Nurse"
        LAB_TECHNICIAN = "lab_technician", "Lab Technician"
        PHARMACIST = "pharmacist", "Pharmacist"
        RECEPTIONIST = "receptionist", "Receptionist"
        PATIENT = "patient", "Patient"

    username = None
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.DOCTOR, db_index=True
    )
    hospital = models.ForeignKey(
        "Hospital", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="users", help_text="Primary hospital affiliation"
    )
    national_health_id = models.CharField(
        max_length=50, unique=True, null=True, blank=True, db_index=True,
        help_text="National patient identifier (for patient-role users)"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r"^\+?1?\d{9,15}$")],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email", "role"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"


# ─── Patient Model ───
class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    class BloodGroup(models.TextChoices):
        A_POSITIVE = "A+", "A+"
        A_NEGATIVE = "A-", "A-"
        B_POSITIVE = "B+", "B+"
        B_NEGATIVE = "B-", "B-"
        AB_POSITIVE = "AB+", "AB+"
        AB_NEGATIVE = "AB-", "AB-"
        O_POSITIVE = "O+", "O+"
        O_NEGATIVE = "O-", "O-"
        UNKNOWN = "unknown", "Unknown"

    id = models.BigAutoField(primary_key=True)
    health_id = models.CharField(
        max_length=18, unique=True, editable=False, db_index=True
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    national_id = models.CharField(
        max_length=50, unique=True, null=True, blank=True, db_index=True
    )
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.choices, db_index=True)
    phone_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r"^\+?1?\d{9,15}$")],
    )
    email = models.EmailField(max_length=255, null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    blood_group = models.CharField(
        max_length=10, choices=BloodGroup.choices, default=BloodGroup.UNKNOWN
    )
    allergies = models.TextField(blank=True, help_text="Comma-separated list")
    chronic_conditions = models.TextField(
        blank=True, help_text="Comma-separated list"
    )
    qr_code = models.TextField(blank=True, editable=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="patients_created"
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="patients_updated"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "patients"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["health_id"]),
            models.Index(fields=["first_name", "last_name"]),
            models.Index(fields=["national_id"]),
            models.Index(fields=["date_of_birth"]),
            models.Index(fields=["gender"]),
            models.Index(fields=["created_at"]),
        ]

    def generate_health_id(self):
        raw = f"{self.first_name[:2].upper()}{uuid.uuid4().hex[:12].upper()}"
        return f"EHR-{raw[:4]}-{raw[4:8]}-{raw[8:]}"

    def generate_qr_data(self):
        return json.dumps({
            "health_id": self.health_id,
            "name": f"{self.first_name} {self.last_name}",
            "dob": self.date_of_birth.isoformat(),
        })

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def save(self, *args, **kwargs):
        if not self.health_id:
            self.health_id = self.generate_health_id()
        if not self.qr_code:
            self.qr_code = self.generate_qr_data()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = date.today()
        born = self.date_of_birth
        return (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )

    def __str__(self):
        return f"{self.health_id} - {self.full_name}"


# ─── Patient History (Medical Records Foundation) ───
class PatientHistory(models.Model):
    class RecordType(models.TextChoices):
        DIAGNOSIS = "diagnosis", "Diagnosis"
        MEDICATION = "medication", "Medication"
        LAB_RESULT = "lab_result", "Lab Result"
        PROCEDURE = "procedure", "Procedure"
        VITAL_SIGN = "vital_sign", "Vital Sign"
        NOTE = "note", "Clinical Note"
        ALLERGY = "allergy", "Allergy"
        IMMUNIZATION = "immunization", "Immunization"

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="medical_history"
    )
    record_type = models.CharField(
        max_length=20, choices=RecordType.choices, db_index=True
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="recorded_history"
    )
    recorded_at = models.DateTimeField(default=timezone.now)
    is_confidential = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patient_history"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["patient", "record_type"]),
            models.Index(fields=["patient", "recorded_at"]),
            models.Index(fields=["recorded_by"]),
            models.Index(fields=["record_type"]),
        ]

    def __str__(self):
        return f"{self.patient.health_id} - {self.get_record_type_display()} - {self.title}"


# ─── Audit Log ───
class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        READ = "read", "Read"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        LOGIN_FAILED = "login_failed", "Login Failed"
        PERMISSION_DENIED = "permission_denied", "Permission Denied"
        EXPORT = "export", "Export"

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, db_index=True
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.TextField(blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self):
        return f"{self.created_at} - {self.user} - {self.action} - {self.resource_type}"


# ─── Visit / Encounter ───
class Visit(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        FOLLOW_UP = "follow_up", "Follow Up"

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="visits"
    )
    doctor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="visits_conducted"
    )
    visit_date = models.DateTimeField(default=timezone.now, db_index=True)
    chief_complaint = models.TextField(blank=True)
    symptoms = models.TextField(blank=True, help_text="Comma-separated or structured")
    diagnosis_summary = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS, db_index=True
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="visits_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "visits"
        ordering = ["-visit_date"]
        indexes = [
            models.Index(fields=["patient", "visit_date"]),
            models.Index(fields=["doctor", "visit_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["visit_date"]),
        ]

    def __str__(self):
        return f"Visit {self.id} - {self.patient.health_id} - {self.visit_date.date()}"


# ─── Vital Signs ───
class VitalSign(models.Model):
    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name="vital_signs"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="vital_signs"
    )
    temperature = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Celsius"
    )
    blood_pressure_systolic = models.IntegerField(
        null=True, blank=True, help_text="mmHg"
    )
    blood_pressure_diastolic = models.IntegerField(
        null=True, blank=True, help_text="mmHg"
    )
    pulse_rate = models.IntegerField(null=True, blank=True, help_text="bpm")
    respiratory_rate = models.IntegerField(null=True, blank=True, help_text="breaths/min")
    oxygen_saturation = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, help_text="%"
    )
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, help_text="kg"
    )
    height = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, help_text="cm"
    )
    bmi = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="vitals_recorded"
    )
    recorded_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vital_signs"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["patient", "recorded_at"]),
            models.Index(fields=["visit"]),
        ]

    def calculate_bmi(self):
        if self.weight and self.height and self.height > 0:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 1)
        return None

    def save(self, *args, **kwargs):
        if not self.bmi:
            self.bmi = self.calculate_bmi()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vitals {self.id} - {self.patient.health_id} - {self.recorded_at.date()}"


# ─── Diagnosis ───
class Diagnosis(models.Model):
    class Severity(models.TextChoices):
        MILD = "mild", "Mild"
        MODERATE = "moderate", "Moderate"
        SEVERE = "severe", "Severe"
        CRITICAL = "critical", "Critical"

    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name="diagnoses"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="diagnoses"
    )
    diagnosis_type = models.CharField(
        max_length=20, choices=[("primary", "Primary"), ("secondary", "Secondary")],
        default="primary"
    )
    diagnosis_name = models.CharField(max_length=500)
    icd_code = models.CharField(max_length=20, blank=True, db_index=True)
    severity = models.CharField(
        max_length=20, choices=Severity.choices, default=Severity.MODERATE
    )
    clinical_notes = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)
    diagnosed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="diagnoses_made"
    )
    diagnosed_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "diagnoses"
        ordering = ["-diagnosed_at"]
        indexes = [
            models.Index(fields=["patient", "diagnosed_at"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["icd_code"]),
            models.Index(fields=["diagnosis_name"]),
        ]

    def __str__(self):
        return f"{self.diagnosis_name} ({self.patient.health_id})"


# ─── Prescription ───
class Prescription(models.Model):
    class Frequency(models.TextChoices):
        OD = "od", "Once Daily"
        BD = "bd", "Twice Daily"
        TDS = "tds", "Three Times Daily"
        QID = "qid", "Four Times Daily"
        QHS = "qhs", "At Bedtime"
        PRN = "prn", "As Needed"
        STAT = "stat", "Immediately"

    class Route(models.TextChoices):
        ORAL = "oral", "Oral"
        IV = "iv", "Intravenous"
        IM = "im", "Intramuscular"
        SC = "sc", "Subcutaneous"
        TOPICAL = "topical", "Topical"
        INHALATION = "inhalation", "Inhalation"
        SUBLINGUAL = "sublingual", "Sublingual"
        RECTAL = "rectal", "Rectal"
        OPHTHALMIC = "ophthalmic", "Ophthalmic"
        OTIC = "otic", "Otic"

    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name="prescriptions"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="prescriptions"
    )
    medication_name = models.CharField(max_length=300, db_index=True)
    dosage = models.CharField(max_length=100, help_text="e.g. 500mg")
    frequency = models.CharField(
        max_length=10, choices=Frequency.choices, default=Frequency.BD
    )
    duration_days = models.IntegerField(null=True, blank=True)
    duration_text = models.CharField(max_length=100, blank=True)
    route = models.CharField(
        max_length=20, choices=Route.choices, default=Route.ORAL
    )
    instructions = models.TextField(blank=True)
    prescribed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="prescriptions_written"
    )
    prescribed_at = models.DateTimeField(default=timezone.now)
    is_dispensed = models.BooleanField(default=False)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    dispensed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="medications_dispensed"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "prescriptions"
        ordering = ["-prescribed_at"]
        indexes = [
            models.Index(fields=["patient", "prescribed_at"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["medication_name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.medication_name} {self.dosage} - {self.patient.health_id}"


# ─── Lab Request ───
class LabRequest(models.Model):
    class Priority(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"
        STAT = "stat", "STAT"

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        SAMPLE_COLLECTED = "sample_collected", "Sample Collected"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name="lab_requests"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="lab_requests"
    )
    test_name = models.CharField(max_length=300, db_index=True)
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.ROUTINE
    )
    clinical_notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.REQUESTED, db_index=True
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="lab_requests_made"
    )
    requested_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lab_requests"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["test_name"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.test_name} - {self.patient.health_id} ({self.status})"


# ─── Lab Result ───
class LabResult(models.Model):
    lab_request = models.OneToOneField(
        LabRequest, on_delete=models.CASCADE, related_name="result"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="lab_results"
    )
    result_data = models.JSONField(default=dict, blank=True)
    result_text = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    is_abnormal = models.BooleanField(default=False)
    file_attachment = models.FileField(
        upload_to="lab_results/", null=True, blank=True
    )
    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="lab_results_processed"
    )
    result_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lab_results"
        ordering = ["-result_at"]
        indexes = [
            models.Index(fields=["patient", "result_at"]),
            models.Index(fields=["lab_request"]),
            models.Index(fields=["is_abnormal"]),
        ]

    def __str__(self):
        return f"Result {self.lab_request.test_name} - {self.patient.health_id}"


# ─── Ward ───
class Ward(models.Model):
    class WardType(models.TextChoices):
        GENERAL = "general", "General"
        PRIVATE = "private", "Private"
        ICU = "icu", "ICU"
        PEDIATRICS = "pediatrics", "Pediatrics"
        MATERNITY = "maternity", "Maternity"
        SURGERY = "surgery", "Surgery"
        ISOLATION = "isolation", "Isolation"

    ward_name = models.CharField(max_length=200)
    ward_type = models.CharField(
        max_length=20, choices=WardType.choices, default=WardType.GENERAL, db_index=True
    )
    capacity = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wards"
        indexes = [models.Index(fields=["ward_type"])]

    @property
    def available_beds(self):
        return self.beds.filter(occupancy_status=Bed.Status.AVAILABLE).count()

    @property
    def occupied_beds(self):
        return self.beds.filter(occupancy_status=Bed.Status.OCCUPIED).count()

    def __str__(self):
        return f"{self.ward_name} ({self.get_ward_type_display()})"


# ─── Bed ───
class Bed(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        OCCUPIED = "occupied", "Occupied"
        MAINTENANCE = "maintenance", "Maintenance"

    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="beds")
    bed_number = models.CharField(max_length=20)
    occupancy_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE, db_index=True
    )

    class Meta:
        db_table = "beds"
        unique_together = ["ward", "bed_number"]
        indexes = [models.Index(fields=["occupancy_status"])]

    def __str__(self):
        return f"{self.ward.ward_name} - Bed {self.bed_number} ({self.get_occupancy_status_display()})"


# ─── Admission ───
class Admission(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DISCHARGED = "discharged", "Discharged"
        TRANSFERRED = "transferred", "Transferred"

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="admissions"
    )
    admitted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="admissions_made"
    )
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, related_name="admissions")
    bed = models.OneToOneField(
        Bed, on_delete=models.SET_NULL, null=True, related_name="current_admission"
    )
    admission_reason = models.TextField(blank=True)
    admission_date = models.DateTimeField(default=timezone.now, db_index=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    discharged_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="discharges_made"
    )
    discharge_notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admissions"
        ordering = ["-admission_date"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["ward", "status"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Admission {self.id} - {self.patient.health_id} ({self.get_status_display()})"


# ─── Invoice ───
class Invoice(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        PARTIALLY_PAID = "partially_paid", "Partially Paid"
        CANCELLED = "cancelled", "Cancelled"

    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="invoices"
    )
    visit = models.ForeignKey(
        Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices"
    )
    admission = models.ForeignKey(
        Admission, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices"
    )
    consultation_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lab_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pharmacy_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    admission_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    radiology_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    insurance_provider = models.CharField(max_length=200, blank=True)
    insurance_policy_no = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="invoices_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["status"]),
        ]

    def calculate_totals(self):
        subtotal = (
            self.consultation_fee + self.lab_fee + self.pharmacy_fee +
            self.admission_fee + self.radiology_fee + self.other_fees
        )
        self.total_amount = subtotal - self.discount + self.tax
        self.balance = self.total_amount - self.amount_paid
        if self.balance <= 0 and self.total_amount > 0:
            self.status = Invoice.Status.PAID
        elif self.amount_paid > 0 and self.balance > 0:
            self.status = Invoice.Status.PARTIALLY_PAID

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            prefix = "INV"
            import random
            self.invoice_number = f"{prefix}-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        self.calculate_totals()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.patient.health_id} ({self.get_status_display()})"


# ─── Payment ───
class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        MPESA = "mpesa", "M-Pesa"
        INSURANCE = "insurance", "Insurance"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="payments"
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=20, choices=Method.choices, default=Method.CASH
    )
    transaction_reference = models.CharField(max_length=200, blank=True)
    payment_date = models.DateTimeField(default=timezone.now)
    received_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="payments_received"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"
        ordering = ["-payment_date"]
        indexes = [
            models.Index(fields=["invoice"]),
            models.Index(fields=["payment_method"]),
            models.Index(fields=["payment_date"]),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_invoice()

    def _update_invoice(self):
        total_paid = Payment.objects.filter(invoice=self.invoice).aggregate(
            total=models.Sum("amount_paid")
        )["total"] or 0
        self.invoice.amount_paid = total_paid
        self.invoice.save(update_fields=["amount_paid", "balance", "status"])

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.amount_paid} ({self.get_payment_method_display()})"


# ─── Imaging Request ───
class ImagingRequest(models.Model):
    class ImagingType(models.TextChoices):
        X_RAY = "xray", "X-Ray"
        MRI = "mri", "MRI"
        CT_SCAN = "ct_scan", "CT Scan"
        ULTRASOUND = "ultrasound", "Ultrasound"
        MAMMOGRAPHY = "mammography", "Mammography"
        PET_SCAN = "pet_scan", "PET Scan"

    class Priority(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"
        STAT = "stat", "STAT"

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name="imaging_requests"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="imaging_requests"
    )
    imaging_type = models.CharField(
        max_length=20, choices=ImagingType.choices, default=ImagingType.X_RAY, db_index=True
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.ROUTINE
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.REQUESTED, db_index=True
    )
    clinical_history = models.TextField(blank=True)
    region_examined = models.CharField(max_length=300, blank=True)
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="imaging_requests_made"
    )
    requested_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "imaging_requests"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["imaging_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.get_imaging_type_display()} - {self.patient.health_id}"


# ─── Imaging Result ───
class ImagingResult(models.Model):
    imaging_request = models.OneToOneField(
        ImagingRequest, on_delete=models.CASCADE, related_name="result"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="imaging_results"
    )
    findings = models.TextField(blank=True)
    impression = models.TextField(blank=True)
    report = models.TextField(blank=True)
    radiologist = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="imaging_reports"
    )
    image_file = models.FileField(upload_to="imaging/", null=True, blank=True)
    report_file = models.FileField(upload_to="imaging_reports/", null=True, blank=True)
    is_abnormal = models.BooleanField(default=False)
    result_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "imaging_results"
        ordering = ["-result_at"]
        indexes = [
            models.Index(fields=["patient", "result_at"]),
            models.Index(fields=["is_abnormal"]),
        ]

    def __str__(self):
        return f"Imaging Result {self.imaging_request.get_imaging_type_display()} - {self.patient.health_id}"


# ─── Notification ───
class Notification(models.Model):
    class Category(models.TextChoices):
        LAB_RESULT = "lab_result", "Lab Result"
        IMAGING = "imaging", "Imaging"
        ADMISSION = "admission", "Admission"
        BILLING = "billing", "Billing"
        APPOINTMENT = "appointment", "Appointment"
        GENERAL = "general", "General"

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications", db_index=True
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications"
    )
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.GENERAL, db_index=True
    )
    title = models.CharField(max_length=300)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    link = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient.email}"


# ═══════════════════════════════════════════════════════════════
# PHASE 4 — NATIONAL HEALTH INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════

# ─── Hospital (Multi-Tenant Tenant) ───
class Hospital(models.Model):
    class HospitalType(models.TextChoices):
        NATIONAL_REFERRAL = "national_referral", "National Referral Hospital"
        COUNTY_REFERRAL = "county_referral", "County Referral Hospital"
        COUNTY = "county", "County Hospital"
        SUB_COUNTY = "sub_county", "Sub-County Hospital"
        PRIVATE = "private", "Private Hospital"
        MISSION = "mission", "Mission Hospital"
        CLINIC = "clinic", "Clinic"

    hospital_name = models.CharField(max_length=300, db_index=True)
    hospital_code = models.CharField(max_length=20, unique=True, db_index=True)
    hospital_type = models.CharField(max_length=20, choices=HospitalType.choices, default=HospitalType.COUNTY)
    county = models.CharField(max_length=100, db_index=True)
    sub_county = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    license_number = models.CharField(max_length=100, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hospitals"
        verbose_name = "Hospital"
        verbose_name_plural = "Hospitals"
        indexes = [
            models.Index(fields=["hospital_code"]),
            models.Index(fields=["county", "hospital_type"]),
        ]

    def __str__(self):
        return f"{self.hospital_name} ({self.hospital_code})"


# ─── Department ───
class Department(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="departments")
    department_name = models.CharField(max_length=200)
    department_code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "departments"
        unique_together = [["hospital", "department_name"]]
        indexes = [
            models.Index(fields=["hospital", "department_name"]),
        ]

    def __str__(self):
        return f"{self.department_name} - {self.hospital.hospital_code}"


# ─── Hospital Staff (User-Hospital Membership) ───
class HospitalStaff(models.Model):
    class StaffRole(models.TextChoices):
        HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"
        DOCTOR = "doctor", "Doctor"
        NURSE = "nurse", "Nurse"
        LAB_TECHNICIAN = "lab_technician", "Lab Technician"
        PHARMACIST = "pharmacist", "Pharmacist"
        RADIOLOGIST = "radiologist", "Radiologist"
        RECEPTIONIST = "receptionist", "Receptionist"
        ACCOUNTANT = "accountant", "Accountant"
        IT_SUPPORT = "it_support", "IT Support"

    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="hospital_memberships")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="staff_members")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="staff")
    staff_role = models.CharField(max_length=20, choices=StaffRole.choices, db_index=True)
    employee_id = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hospital_staff"
        unique_together = [["user", "hospital"]]
        indexes = [
            models.Index(fields=["hospital", "staff_role"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user.email} @ {self.hospital.hospital_code}"


# ─── National Patient Identity ───
class PatientIdentity(models.Model):
    patient = models.OneToOneField("Patient", on_delete=models.CASCADE, related_name="national_identity")
    national_health_id = models.CharField(max_length=50, unique=True, db_index=True)
    id_type = models.CharField(max_length=20, default="national_id", choices=[
        ("national_id", "National ID"),
        ("passport", "Passport"),
        ("birth_cert", "Birth Certificate"),
        ("alien_card", "Alien Card"),
        ("refugee_id", "Refugee ID"),
    ])
    id_number = models.CharField(max_length=50, db_index=True)
    verified = models.BooleanField(default=False)
    verification_source = models.CharField(max_length=100, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patient_identities"
        indexes = [
            models.Index(fields=["national_health_id"]),
            models.Index(fields=["id_number", "id_type"]),
        ]

    def __str__(self):
        return f"{self.national_health_id} - {self.patient.full_name}"


# ─── Patient Merge Log ───
class PatientMergeLog(models.Model):
    merged_into = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="merge_targets")
    merged_from = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="merge_sources")
    merged_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True)
    merge_reason = models.TextField(blank=True)
    merged_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patient_merge_logs"
        indexes = [
            models.Index(fields=["merged_into", "created_at"]),
        ]


# ─── Referral (Cross-Hospital) ───
class Referral(models.Model):
    class ReferralPriority(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"
        EMERGENCY = "emergency", "Emergency"

    class ReferralStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="referrals")
    referring_hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="outgoing_referrals")
    referring_doctor = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, related_name="referrals_made")
    receiving_hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="incoming_referrals")
    receiving_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=ReferralPriority.choices, default=ReferralPriority.ROUTINE)
    status = models.CharField(max_length=20, choices=ReferralStatus.choices, default=ReferralStatus.PENDING, db_index=True)
    clinical_summary = models.TextField()
    reason_for_referral = models.TextField()
    referral_notes = models.TextField(blank=True)
    response_notes = models.TextField(blank=True)
    responded_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="referral_responses")
    responded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "referrals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "receiving_hospital"]),
            models.Index(fields=["referring_hospital", "created_at"]),
            models.Index(fields=["patient"]),
        ]

    def __str__(self):
        return f"Referral {self.patient.health_id}: {self.referring_hospital.hospital_code} → {self.receiving_hospital.hospital_code}"


# ─── Referral Document ───
class ReferralDocument(models.Model):
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=50, choices=[
        ("lab_result", "Lab Result"),
        ("imaging", "Imaging Report"),
        ("clinical_notes", "Clinical Notes"),
        ("prescription", "Prescription"),
        ("other", "Other"),
    ])
    file = models.FileField(upload_to="referrals/%Y/%m/")
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "referral_documents"


# ─── Cross-Hospital Access Log ───
class CrossHospitalAccess(models.Model):
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="cross_hospital_accesses")
    requesting_hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="access_requests")
    requesting_user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="cross_hospital_accesses")
    authorized_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="access_authorizations")
    access_reason = models.TextField()
    is_authorized = models.BooleanField(default=False)
    accessed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cross_hospital_access"
        indexes = [
            models.Index(fields=["patient", "requesting_hospital"]),
            models.Index(fields=["is_authorized", "expires_at"]),
        ]


# ─── Sync Queue (Offline-First) ───
class SyncQueue(models.Model):
    class SyncAction(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"

    class SyncStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CONFLICT = "conflict", "Conflict"

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="sync_queue")
    device_id = models.CharField(max_length=100, blank=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=50, blank=True)
    action = models.CharField(max_length=20, choices=SyncAction.choices)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=SyncStatus.choices, default=SyncStatus.PENDING, db_index=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    conflict_resolution = models.CharField(max_length=20, default="last_write_wins", choices=[
        ("last_write_wins", "Last Write Wins"),
        ("manual", "Manual Resolution"),
    ])
    client_timestamp = models.DateTimeField()
    server_timestamp = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "sync_queue"
        ordering = ["-server_timestamp"]
        indexes = [
            models.Index(fields=["hospital", "status"]),
            models.Index(fields=["status", "retry_count"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self):
        return f"{self.action} {self.resource_type}#{self.resource_id} [{self.status}]"


# ─── Sync Log ───
class SyncLog(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="sync_logs")
    device_id = models.CharField(max_length=100, blank=True)
    items_processed = models.IntegerField(default=0)
    items_failed = models.IntegerField(default=0)
    duration_ms = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ("success", "Success"),
        ("partial", "Partial"),
        ("failed", "Failed"),
    ])
    details = models.JSONField(default=dict)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sync_logs"
        ordering = ["-completed_at"]


# ─── Insurance Profile (SHA Readiness) ───
class InsuranceProfile(models.Model):
    class InsuranceProvider(models.TextChoices):
        SHA = "sha", "SHA - Social Health Authority"
        NHIF = "nhif", "NHIF (Legacy)"
        PRIVATE = "private", "Private Insurance"
        COMMUNITY = "community", "Community Health Fund"

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="insurance_profiles")
    provider = models.CharField(max_length=20, choices=InsuranceProvider.choices)
    policy_number = models.CharField(max_length=100, db_index=True)
    member_number = models.CharField(max_length=100, blank=True)
    dependent_number = models.CharField(max_length=50, blank=True)
    coverage_type = models.CharField(max_length=50, default="inpatient", choices=[
        ("inpatient", "Inpatient"),
        ("outpatient", "Outpatient"),
        ("comprehensive", "Comprehensive"),
        ("maternity", "Maternity"),
        ("chronic", "Chronic Illness"),
    ])
    is_active = models.BooleanField(default=True, db_index=True)
    verified = models.BooleanField(default=False)
    verification_data = models.JSONField(default=dict)
    coverage_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductible = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "insurance_profiles"
        indexes = [
            models.Index(fields=["patient", "is_active"]),
            models.Index(fields=["policy_number"]),
            models.Index(fields=["provider", "is_active"]),
        ]

    def __str__(self):
        return f"{self.get_provider_display()} {self.policy_number} - {self.patient.health_id}"


# ─── Insurance Claim ───
class InsuranceClaim(models.Model):
    class ClaimStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        PAID = "paid", "Paid"

    insurance_profile = models.ForeignKey(InsuranceProfile, on_delete=models.CASCADE, related_name="claims")
    invoice = models.ForeignKey("Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="insurance_claims")
    claim_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=ClaimStatus.choices, default=ClaimStatus.DRAFT, db_index=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    claim_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "insurance_claims"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["insurance_profile", "status"]),
        ]

    def __str__(self):
        return f"Claim {self.claim_number} - {self.status}"


# ─── Telemedicine Session ───
class TelemedicineSession(models.Model):
    class SessionStatus(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        MISSED = "missed", "Missed"

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="telemedicine_sessions")
    doctor = models.ForeignKey("User", on_delete=models.CASCADE, related_name="telemedicine_sessions")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="telemedicine_sessions")
    scheduled_at = models.DateTimeField(db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.SCHEDULED, db_index=True)
    session_type = models.CharField(max_length=20, default="video", choices=[
        ("video", "Video Call"),
        ("audio", "Audio Call"),
        ("chat", "Text Chat"),
    ])
    consultation_notes = models.TextField(blank=True)
    meeting_url = models.CharField(max_length=500, blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "telemedicine_sessions"
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(fields=["doctor", "scheduled_at"]),
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["hospital", "status"]),
        ]

    def __str__(self):
        return f"Telemed {self.patient.health_id} - Dr.{self.doctor.id} [{self.status}]"


# ─── Enterprise Audit Event ───
class EnterpriseAuditEvent(models.Model):
    class EventType(models.TextChoices):
        DATA_ACCESS = "data_access", "Data Access"
        SECURITY = "security", "Security Event"
        ADMIN = "admin", "Admin Action"
        SYSTEM = "system", "System Event"
        INTEGRATION = "integration", "Integration Event"
        SYNC = "sync", "Sync Event"

    event_type = models.CharField(max_length=20, choices=EventType.choices, db_index=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, null=True, blank=True, related_name="audit_events")
    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True)
    actor_type = models.CharField(max_length=20, choices=[
        ("user", "User"),
        ("system", "System"),
        ("api", "API"),
        ("integration", "Integration"),
    ], default="user")
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=50, blank=True)
    action = models.CharField(max_length=50)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    severity = models.CharField(max_length=20, default="info", choices=[
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("critical", "Critical"),
    ])
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "enterprise_audit_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["hospital", "event_type"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["severity"]),
        ]

    def __str__(self):
        return f"[{self.event_type}] {self.action} - {self.resource_type}#{self.resource_id}"


# ═══════════════════════════════════════════════════════════════
# PHASE 5 — ENTERPRISE CYBERSECURITY, AI READINESS & OBSERVABILITY
# ═══════════════════════════════════════════════════════════════

# ─── Security Event / Intrusion Detection ───
class SecurityEvent(models.Model):
    class EventCategory(models.TextChoices):
        LOGIN_ATTEMPT = "login_attempt", "Login Attempt"
        SUSPICIOUS_ACTIVITY = "suspicious_activity", "Suspicious Activity"
        ANOMALY = "anomaly", "Anomaly Detection"
        INTRUSION = "intrusion", "Intrusion Attempt"
        POLICY_VIOLATION = "policy_violation", "Policy Violation"
        RATE_LIMIT = "rate_limit", "Rate Limit Exceeded"
        AUTH_FAILURE = "auth_failure", "Authentication Failure"
        TOKEN_ANOMALY = "token_anomaly", "Token Anomaly"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    category = models.CharField(max_length=30, choices=EventCategory.choices, db_index=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.INFO)
    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True)
    hospital = models.ForeignKey("Hospital", on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    risk_score = models.FloatField(default=0.0)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="security_resolutions")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "security_events"
        ordering = ["-detected_at"]
        indexes = [
            models.Index(fields=["category", "severity"]),
            models.Index(fields=["risk_score"]),
            models.Index(fields=["ip_address"]),
            models.Index(fields=["detected_at"]),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.category} - score:{self.risk_score}"


# ─── Device Fingerprint ───
class DeviceFingerprint(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="devices")
    fingerprint_hash = models.CharField(max_length=255, db_index=True)
    device_name = models.CharField(max_length=255, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=100, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    is_trusted = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(auto_now=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    risk_count = models.IntegerField(default=0)

    class Meta:
        db_table = "device_fingerprints"
        unique_together = [["user", "fingerprint_hash"]]
        indexes = [
            models.Index(fields=["user", "is_trusted"]),
        ]

    def __str__(self):
        return f"{self.device_name or 'Unknown'} ({self.user.email})"


# ─── MFAToken ───
class MFAToken(models.Model):
    class TokenType(models.TextChoices):
        TOTP = "totp", "Time-based OTP"
        EMAIL = "email", "Email OTP"
        SMS = "sms", "SMS OTP"
        BACKUP = "backup", "Backup Code"

    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="mfa_tokens")
    token_type = models.CharField(max_length=10, choices=TokenType.choices)
    secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mfa_tokens"


# ─── Consent Log (Compliance) ───
class ConsentLog(models.Model):
    class ConsentType(models.TextChoices):
        DATA_PROCESSING = "data_processing", "Data Processing"
        DATA_SHARING = "data_sharing", "Data Sharing"
        RESEARCH = "research", "Research Use"
        MARKETING = "marketing", "Marketing Communications"
        TELEMEDICINE = "telemedicine", "Telemedicine Consent"

    class ConsentStatus(models.TextChoices):
        GRANTED = "granted", "Granted"
        REVOKED = "revoked", "Revoked"
        EXPIRED = "expired", "Expired"

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="consents")
    consent_type = models.CharField(max_length=30, choices=ConsentType.choices, db_index=True)
    status = models.CharField(max_length=10, choices=ConsentStatus.choices, default=ConsentStatus.GRANTED)
    granted_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, related_name="consents_granted")
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(blank=True)
    consent_version = models.CharField(max_length=20, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = "consent_logs"
        ordering = ["-granted_at"]
        indexes = [
            models.Index(fields=["patient", "consent_type", "status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.get_consent_type_display()} - {self.patient.health_id} [{self.status}]"


# ─── AIServiceRegistry ───
class AIServiceRegistry(models.Model):
    class ServiceStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        DEGRADED = "degraded", "Degraded"
        ERROR = "error", "Error"

    service_name = models.CharField(max_length=200, unique=True)
    service_version = models.CharField(max_length=20)
    service_type = models.CharField(max_length=50, choices=[
        ("diagnosis", "Diagnosis Assistance"),
        ("risk_prediction", "Risk Prediction"),
        ("anomaly_detection", "Anomaly Detection"),
        ("nlp", "Natural Language Processing"),
        ("imaging", "Imaging Analysis"),
        ("recommendation", "Treatment Recommendation"),
        ("other", "Other"),
    ])
    endpoint_url = models.CharField(max_length=500, blank=True)
    api_key_hash = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=ServiceStatus.choices, default=ServiceStatus.INACTIVE)
    config = models.JSONField(default=dict)
    metrics = models.JSONField(default=dict)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_service_registry"
        indexes = [
            models.Index(fields=["service_type", "status"]),
        ]

    def __str__(self):
        return f"{self.service_name} v{self.service_version} [{self.status}]"


# ─── System Health Metric ───
class SystemHealthMetric(models.Model):
    class MetricType(models.TextChoices):
        API_LATENCY = "api_latency", "API Latency"
        DB_QUERY_TIME = "db_query_time", "Database Query Time"
        CACHE_HIT_RATIO = "cache_hit_ratio", "Cache Hit Ratio"
        QUEUE_DEPTH = "queue_depth", "Queue Depth"
        CPU_USAGE = "cpu_usage", "CPU Usage"
        MEMORY_USAGE = "memory_usage", "Memory Usage"
        DISK_USAGE = "disk_usage", "Disk Usage"
        ACTIVE_USERS = "active_users", "Active Users"
        API_REQUESTS = "api_requests", "API Requests"
        ERROR_RATE = "error_rate", "Error Rate"
        SYNC_LAG = "sync_lag", "Synchronization Lag"

    metric_type = models.CharField(max_length=30, choices=MetricType.choices, db_index=True)
    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, null=True, blank=True, related_name="metrics")
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)
    tags = models.JSONField(default=dict)
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "system_health_metrics"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["metric_type", "recorded_at"]),
            models.Index(fields=["hospital", "metric_type"]),
        ]

    def __str__(self):
        return f"{self.metric_type}: {self.value}{self.unit}"


# ─── Analytics Event (Public Health / Feature Pipeline) ───
class AnalyticsEvent(models.Model):
    class EventType(models.TextChoices):
        PATIENT_ADMITTED = "patient_admitted", "Patient Admitted"
        PATIENT_DISCHARGED = "patient_discharged", "Patient Discharged"
        DIAGNOSIS_RECORDED = "diagnosis_recorded", "Diagnosis Recorded"
        LAB_COMPLETED = "lab_completed", "Lab Completed"
        PRESCRIPTION_ISSUED = "prescription_issued", "Prescription Issued"
        REFERRAL_MADE = "referral_made", "Referral Made"
        VISIT_STARTED = "visit_started", "Visit Started"
        VISIT_CLOSED = "visit_closed", "Visit Closed"
        IMAGING_COMPLETED = "imaging_completed", "Imaging Completed"

    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, null=True, blank=True)
    patient = models.ForeignKey("Patient", on_delete=models.SET_NULL, null=True, blank=True)
    anonymized = models.BooleanField(default=False)
    event_data = models.JSONField(default=dict)
    county = models.CharField(max_length=100, blank=True, db_index=True)
    occurred_at = models.DateTimeField(db_index=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_events"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["event_type", "occurred_at"]),
            models.Index(fields=["county", "event_type"]),
            models.Index(fields=["hospital", "event_type"]),
        ]


# ─── External System Integration Registry ───
class ExternalSystem(models.Model):
    class SystemType(models.TextChoices):
        FHIR = "fhir", "FHIR API"
        HL7 = "hl7", "HL7 v2"
        INSURANCE = "insurance", "Insurance Gateway"
        LAB = "lab", "External Laboratory"
        PHARMACY = "pharmacy", "External Pharmacy"
        GOVERNMENT = "government", "Government System"
        MOBILE = "mobile", "Mobile Health App"
        OTHER = "other", "Other"

    system_name = models.CharField(max_length=200)
    system_type = models.CharField(max_length=20, choices=SystemType.choices, db_index=True)
    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, null=True, blank=True, related_name="external_systems")
    base_url = models.CharField(max_length=500)
    api_key_hash = models.CharField(max_length=255, blank=True)
    auth_type = models.CharField(max_length=50, default="api_key", choices=[
        ("api_key", "API Key"),
        ("oauth2", "OAuth 2.0"),
        ("basic", "Basic Auth"),
        ("mutual_tls", "Mutual TLS"),
        ("none", "No Auth"),
    ])
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "external_systems"
        indexes = [
            models.Index(fields=["system_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.system_name} ({self.get_system_type_display()})"


# ═══════════════════════════════════════════════════════════════
# PHASE 6 — AI ASSISTANCE, WEARABLE, BIOMETRIC, PUBLIC HEALTH
# ═══════════════════════════════════════════════════════════════

# ─── Wearable Device ───
class WearableDevice(models.Model):
    class DeviceType(models.TextChoices):
        SMARTWATCH = "smartwatch", "Smart Watch"
        FITNESS_BAND = "fitness_band", "Fitness Band"
        GLUCOSE_MONITOR = "glucose_monitor", "Continuous Glucose Monitor"
        BLOOD_PRESSURE = "blood_pressure", "Blood Pressure Monitor"
        HEART_RATE = "heart_rate", "Heart Rate Monitor"
        PULSE_OXIMETER = "pulse_oximeter", "Pulse Oximeter"
        ECG = "ecg", "ECG Monitor"
        OTHER = "other", "Other"

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="wearable_devices")
    device_type = models.CharField(max_length=30, choices=DeviceType.choices)
    device_name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=200, blank=True, unique=True)
    firmware_version = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    pairing_token = models.CharField(max_length=255, blank=True)
    config = models.JSONField(default=dict)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wearable_devices"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "is_active"]),
            models.Index(fields=["device_type"]),
            models.Index(fields=["serial_number"]),
        ]

    def __str__(self):
        return f"{self.get_device_type_display()} - {self.device_name} ({self.patient.health_id})"


# ─── Device Reading (Wearable / IoT) ───
class DeviceReading(models.Model):
    class ReadingType(models.TextChoices):
        HEART_RATE = "heart_rate", "Heart Rate"
        BLOOD_PRESSURE = "blood_pressure", "Blood Pressure"
        OXYGEN_SATURATION = "oxygen_saturation", "Oxygen Saturation"
        GLUCOSE = "glucose", "Blood Glucose"
        TEMPERATURE = "temperature", "Body Temperature"
        STEPS = "steps", "Step Count"
        CALORIES = "calories", "Calories Burned"
        SLEEP = "sleep", "Sleep Data"
        ECG = "ecg", "ECG Reading"
        WEIGHT = "weight", "Weight"
        FALL = "fall", "Fall Detection"
        LOCATION = "location", "Location"
        OTHER = "other", "Other"

    device = models.ForeignKey(WearableDevice, on_delete=models.CASCADE, related_name="readings")
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="device_readings")
    reading_type = models.CharField(max_length=30, choices=ReadingType.choices, db_index=True)
    value = models.FloatField()
    unit = models.CharField(max_length=50, blank=True)
    metadata = models.JSONField(default=dict)
    recorded_at = models.DateTimeField(db_index=True)
    ingested_at = models.DateTimeField(auto_now_add=True)
    is_abnormal = models.BooleanField(default=False)
    alert_generated = models.BooleanField(default=False)

    class Meta:
        db_table = "device_readings"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["patient", "reading_type", "recorded_at"]),
            models.Index(fields=["device", "recorded_at"]),
            models.Index(fields=["is_abnormal"]),
            models.Index(fields=["recorded_at"]),
        ]

    def __str__(self):
        return f"{self.get_reading_type_display()}: {self.value}{self.unit}"


# ─── AI Insight (Clinical Decision Support) ───
class AIInsight(models.Model):
    class InsightType(models.TextChoices):
        RISK_ASSESSMENT = "risk_assessment", "Risk Assessment"
        DIAGNOSIS_SUGGESTION = "diagnosis_suggestion", "Diagnosis Suggestion"
        MEDICATION_CHECK = "medication_check", "Medication Interaction Check"
        DETERIORATION_ALERT = "deterioration_alert", "Deterioration Alert"
        TREATMENT_RECOMMENDATION = "treatment_recommendation", "Treatment Recommendation"
        ANOMALY_DETECTION = "anomaly_detection", "Anomaly Detection"
        CLINICAL_SUMMARY = "clinical_summary", "Clinical Summary"

    class Confidence(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    insight_type = models.CharField(max_length=30, choices=InsightType.choices, db_index=True)
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="ai_insights", null=True, blank=True)
    visit = models.ForeignKey("Visit", on_delete=models.CASCADE, null=True, blank=True, related_name="ai_insights")
    title = models.CharField(max_length=300)
    summary = models.TextField()
    details = models.JSONField(default=dict)
    confidence = models.CharField(max_length=10, choices=Confidence.choices, default=Confidence.MEDIUM)
    confidence_score = models.FloatField(default=0.0)
    source_service = models.CharField(max_length=200, blank=True)
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_reviews")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    clinical_action_taken = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_insights"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "insight_type"]),
            models.Index(fields=["insight_type", "confidence"]),
            models.Index(fields=["is_reviewed"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"[{self.get_insight_type_display()}] {self.title} ({self.confidence})"


# ─── Public Health Metric (Aggregate Epidemiology) ───
class PublicHealthMetric(models.Model):
    class MetricCategory(models.TextChoices):
        DISEASE_PREVALENCE = "disease_prevalence", "Disease Prevalence"
        OUTBREAK_SIGNAL = "outbreak_signal", "Outbreak Signal"
        VACCINATION_COVERAGE = "vaccination_coverage", "Vaccination Coverage"
        MORTALITY = "mortality", "Mortality Rate"
        HEALTHCARE_BURDEN = "healthcare_burden", "Healthcare Burden"
        HOSPITAL_CAPACITY = "hospital_capacity", "Hospital Capacity"
        BIRTH_RATE = "birth_rate", "Birth Rate"
        LIFE_EXPECTANCY = "life_expectancy", "Life Expectancy"

    metric_category = models.CharField(max_length=30, choices=MetricCategory.choices, db_index=True)
    county = models.CharField(max_length=100, blank=True, db_index=True)
    sub_county = models.CharField(max_length=100, blank=True)
    disease_code = models.CharField(max_length=20, blank=True, db_index=True)
    disease_name = models.CharField(max_length=200, blank=True)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=50, blank=True)
    population_base = models.IntegerField(default=0)
    sample_size = models.IntegerField(default=0)
    confidence_interval_low = models.FloatField(null=True, blank=True)
    confidence_interval_high = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    period_start = models.DateField(db_index=True)
    period_end = models.DateField(db_index=True)
    is_anonymized = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "public_health_metrics"
        ordering = ["-period_end", "-period_start"]
        indexes = [
            models.Index(fields=["metric_category", "period_start"]),
            models.Index(fields=["county", "metric_category"]),
            models.Index(fields=["disease_code", "period_start"]),
            models.Index(fields=["period_start", "period_end"]),
        ]

    def __str__(self):
        return f"{self.get_metric_category_display()}: {self.metric_value}{self.metric_unit} ({self.county})"


# ─── Biometric Identity ───
class BiometricIdentity(models.Model):
    class BiometricType(models.TextChoices):
        FINGERPRINT = "fingerprint", "Fingerprint"
        FACE = "face", "Facial Recognition"
        IRIS = "iris", "Iris Recognition"

    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="biometrics")
    biometric_type = models.CharField(max_length=20, choices=BiometricType.choices)
    biometric_hash = models.CharField(max_length=255, db_index=True)
    encrypted_template = models.TextField()
    is_active = models.BooleanField(default=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    device_id = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict)
    fail_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "biometric_identities"
        unique_together = [["user", "biometric_type"]]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["biometric_hash"]),
        ]

    def __str__(self):
        return f"{self.get_biometric_type_display()} - {self.user.email}"


# ─── Predictive Alert ───
class PredictiveAlert(models.Model):
    class AlertCategory(models.TextChoices):
        PATIENT_DETERIORATION = "patient_deterioration", "Patient Deterioration"
        HOSPITAL_OVERLOAD = "hospital_overload", "Hospital Overload"
        EQUIPMENT_FAILURE = "equipment_failure", "Equipment Failure"
        EPIDEMIC_WARNING = "epidemic_warning", "Epidemic Warning"
        RESOURCE_SHORTAGE = "resource_shortage", "Resource Shortage"
        ANOMALY = "anomaly", "System Anomaly"
        BED_CRISIS = "bed_crisis", "Bed Capacity Crisis"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"
        EMERGENCY = "emergency", "Emergency"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"
        FALSE_POSITIVE = "false_positive", "False Positive"

    category = models.CharField(max_length=30, choices=AlertCategory.choices, db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.WARNING)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    title = models.CharField(max_length=300)
    description = models.TextField()
    predicted_at = models.DateTimeField(db_index=True)
    confidence_score = models.FloatField(default=0.0)
    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, null=True, blank=True, related_name="predictive_alerts")
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, null=True, blank=True, related_name="predictive_alerts")
    affected_entity_type = models.CharField(max_length=100, blank=True)
    affected_entity_id = models.CharField(max_length=50, blank=True)
    suggested_action = models.TextField(blank=True)
    acknowledged_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="operational_alerts_acknowledged")
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "predictive_alerts"
        ordering = ["-predicted_at"]


# ─── Smart Hospital Device ───
class SmartHospitalDevice(models.Model):
    class DeviceCategory(models.TextChoices):
        SMART_BED = "smart_bed", "Smart Bed"
        INFUSION_PUMP = "infusion_pump", "Infusion Pump"
        VENTILATOR = "ventilator", "Ventilator"
        PATIENT_MONITOR = "patient_monitor", "Patient Monitor"
        TEMPERATURE_SENSOR = "temperature_sensor", "Temperature Sensor"
        DOOR_SENSOR = "door_sensor", "Door Sensor"
        MOTION_SENSOR = "motion_sensor", "Motion Sensor"
        ENVIRONMENTAL = "environmental", "Environmental Sensor"
        OTHER = "other", "Other"

    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, related_name="smart_devices")
    ward = models.ForeignKey("Ward", on_delete=models.SET_NULL, null=True, blank=True, related_name="smart_devices")
    bed = models.ForeignKey("Bed", on_delete=models.SET_NULL, null=True, blank=True, related_name="smart_devices")
    device_category = models.CharField(max_length=30, choices=DeviceCategory.choices)
    device_name = models.CharField(max_length=200)
    serial_number = models.CharField(max_length=200, unique=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=50, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)
    is_online = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "smart_hospital_devices"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hospital", "device_category", "is_active"]),
            models.Index(fields=["is_online"]),
        ]

    def __str__(self):
        return f"{self.get_device_category_display()} - {self.device_name} ({'Online' if self.is_online else 'Offline'})"


# ─── Citizen Health Profile (Portal Extension) ───
class CitizenHealthProfile(models.Model):
    patient = models.OneToOneField("Patient", on_delete=models.CASCADE, related_name="citizen_profile")
    preferred_language = models.CharField(max_length=10, default="en")
    emergency_contacts = models.JSONField(default=list)
    allergies_summary = models.TextField(blank=True)
    chronic_conditions_summary = models.TextField(blank=True)
    medication_summary = models.TextField(blank=True)
    vaccination_summary = models.TextField(blank=True)
    notification_preferences = models.JSONField(default=dict)
    consent_settings = models.JSONField(default=dict)
    portal_enabled = models.BooleanField(default=True)
    last_portal_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "citizen_health_profiles"

    def __str__(self):
        return f"Citizen Profile - {self.patient.health_id}"


# ═══════════════════════════════════════════════════════════════
# PHASE 7 — AI ORCHESTRATION, EPIDEMIC INTELLIGENCE, PRECISION HEALTH
# ═══════════════════════════════════════════════════════════════

# ─── AI Recommendation (Phase 7 Framework) ───
class AIRecommendation(models.Model):
    class RecommendationType(models.TextChoices):
        CLINICAL = "clinical", "Clinical Recommendation"
        MEDICATION = "medication", "Medication Advisory"
        DIAGNOSTIC = "diagnostic", "Diagnostic Suggestion"
        FOLLOW_UP = "follow_up", "Follow-up Plan"
        PREVENTIVE = "preventive", "Preventive Care"
        LIFESTYLE = "lifestyle", "Lifestyle Modification"

    class Priority(models.TextChoices):
        INFORMATION = "information", "Information"
        SUGGESTION = "suggestion", "Suggestion"
        RECOMMENDATION = "recommendation", "Recommendation"
        ALERT = "alert", "Alert"

    recommendation_type = models.CharField(max_length=20, choices=RecommendationType.choices, db_index=True)
    priority = models.CharField(max_length=15, choices=Priority.choices, default=Priority.SUGGESTION)
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="ai_recommendations", null=True, blank=True)
    visit = models.ForeignKey("Visit", on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=300)
    recommendation_text = models.TextField()
    clinical_rationale = models.TextField(blank=True)
    supporting_evidence = models.JSONField(default=list)
    confidence_score = models.FloatField(default=0.0)
    source_service = models.CharField(max_length=200, blank=True)
    is_accepted = models.BooleanField(null=True, blank=True)
    accepted_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="accepted_recommendations")
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_recommendations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "recommendation_type"]),
            models.Index(fields=["priority", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"


# ─── Epidemic Alert (Intelligent Surveillance) ───
class EpidemicAlert(models.Model):
    class AlertLevel(models.TextChoices):
        GREEN = "green", "Normal"
        YELLOW = "yellow", "Watch"
        ORANGE = "orange", "Warning"
        RED = "red", "Emergency"
        CRITICAL = "critical", "Critical"

    class AlertSource(models.TextChoices):
        SYNDROMIC = "syndromic", "Syndromic Surveillance"
        LAB = "lab", "Laboratory Confirmed"
        HOSPITAL = "hospital", "Hospital Reporting"
        PHARMACY = "pharmacy", "Pharmacy Sales"
        SCHOOL = "school", "School Absenteeism"
        WEARABLE = "wearable", "Wearable Device"
        OTHER = "other", "Other"

    alert_level = models.CharField(max_length=10, choices=AlertLevel.choices, default=AlertLevel.YELLOW)
    alert_source = models.CharField(max_length=20, choices=AlertSource.choices, db_index=True)
    disease_code = models.CharField(max_length=20, db_index=True)
    disease_name = models.CharField(max_length=200)
    county = models.CharField(max_length=100, db_index=True)
    sub_county = models.CharField(max_length=100, blank=True)
    location_point = models.JSONField(default=dict)
    confirmed_cases = models.IntegerField(default=0)
    suspected_cases = models.IntegerField(default=0)
    reported_deaths = models.IntegerField(default=0)
    attack_rate = models.FloatField(default=0.0)
    doubling_time_days = models.FloatField(null=True, blank=True)
    r0_estimate = models.FloatField(null=True, blank=True)
    affected_population = models.IntegerField(default=0)
    signal_strength = models.FloatField(default=0.0)
    triggered_by_event = models.CharField(max_length=100, blank=True)
    recommended_actions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    detected_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "epidemic_alerts"
        ordering = ["-detected_at"]
        indexes = [
            models.Index(fields=["alert_level", "county"]),
            models.Index(fields=["disease_code", "detected_at"]),
            models.Index(fields=["county", "alert_level", "is_active"]),
        ]

    def __str__(self):
        return f"[{self.alert_level}] {self.disease_name} - {self.county}"


# ─── Health Risk Profile (Precision Health) ───
class HealthRiskProfile(models.Model):
    class RiskCategory(models.TextChoices):
        CARDIOVASCULAR = "cardiovascular", "Cardiovascular Risk"
        DIABETES = "diabetes", "Diabetes Risk"
        RESPIRATORY = "respiratory", "Respiratory Risk"
        CANCER = "cancer", "Cancer Risk"
        MENTAL_HEALTH = "mental_health", "Mental Health Risk"
        FALL = "fall", "Fall Risk"
        READMISSION = "readmission", "Readmission Risk"
        GENERAL = "general", "General Health Risk"

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="risk_profiles")
    risk_category = models.CharField(max_length=20, choices=RiskCategory.choices, db_index=True)
    risk_score = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=20, choices=[
        ("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("critical", "Critical"),
    ], default="low")
    contributing_factors = models.JSONField(default=list)
    protective_factors = models.JSONField(default=list)
    longitudinal_trend = models.JSONField(default=list)
    last_assessed_at = models.DateTimeField(db_index=True)
    assessment_model = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "health_risk_profiles"
        unique_together = [["patient", "risk_category"]]
        indexes = [
            models.Index(fields=["patient", "risk_level", "is_active"]),
            models.Index(fields=["risk_category", "risk_score"]),
        ]

    def __str__(self):
        return f"{self.get_risk_category_display()}: {self.risk_level} ({self.risk_score:.2f})"


# ─── Smart Device Event (Advanced IoT) ───
class SmartDeviceEvent(models.Model):
    class EventCategory(models.TextChoices):
        PATIENT_ALERT = "patient_alert", "Patient Alert"
        DEVICE_STATUS = "device_status", "Device Status"
        ENVIRONMENTAL = "environmental", "Environmental Reading"
        LOCATION = "location", "Location Update"
        EMERGENCY = "emergency", "Emergency Signal"
        ROUTINE = "routine", "Routine Reading"

    device = models.ForeignKey("SmartHospitalDevice", on_delete=models.CASCADE, related_name="events")
    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, related_name="device_events")
    ward = models.ForeignKey("Ward", on_delete=models.SET_NULL, null=True, blank=True)
    event_category = models.CharField(max_length=20, choices=EventCategory.choices, db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    payload = models.JSONField(default=dict)
    severity = models.CharField(max_length=10, default="info", choices=[
        ("info", "Info"), ("warning", "Warning"), ("critical", "Critical"), ("emergency", "Emergency"),
    ])
    is_processed = models.BooleanField(default=False)
    occurred_at = models.DateTimeField(db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "smart_device_events"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["device", "occurred_at"]),
            models.Index(fields=["hospital", "event_category", "severity"]),
            models.Index(fields=["event_type", "occurred_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} ({self.get_severity_display()})"


# ─── Predictive Metric (Time-series Forecasting) ───
class PredictiveMetric(models.Model):
    class MetricCategory(models.TextChoices):
        HOSPITAL_LOAD = "hospital_load", "Hospital Load"
        PATIENT_FLOW = "patient_flow", "Patient Flow"
        RESOURCE_UTILIZATION = "resource_utilization", "Resource Utilization"
        DISEASE_INCIDENCE = "disease_incidence", "Disease Incidence"
        MORTALITY = "mortality", "Mortality"
        DEMAND = "demand", "Healthcare Demand"
        STAFFING = "staffing", "Staffing Need"

    metric_category = models.CharField(max_length=25, choices=MetricCategory.choices, db_index=True)
    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, null=True, blank=True, related_name="predictive_metrics")
    county = models.CharField(max_length=100, blank=True, db_index=True)
    metric_name = models.CharField(max_length=200)
    predicted_value = models.FloatField()
    actual_value = models.FloatField(null=True, blank=True)
    confidence_interval_lower = models.FloatField(null=True, blank=True)
    confidence_interval_upper = models.FloatField(null=True, blank=True)
    prediction_date = models.DateField(db_index=True)
    forecast_horizon_days = models.IntegerField(default=7)
    model_name = models.CharField(max_length=200, blank=True)
    model_accuracy = models.FloatField(null=True, blank=True)
    features_used = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "predictive_metrics"
        ordering = ["-prediction_date"]
        indexes = [
            models.Index(fields=["metric_category", "prediction_date"]),
            models.Index(fields=["hospital", "metric_category"]),
            models.Index(fields=["county", "metric_category", "prediction_date"]),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.predicted_value} (horizon: {self.forecast_horizon_days}d)"


# ─── Telemedicine Interaction (Session Log) ───
class TelemedicineInteraction(models.Model):
    class InteractionType(models.TextChoices):
        MESSAGE = "message", "Secure Message"
        FILE = "file", "File Transfer"
        PRESCRIPTION = "prescription", "Digital Prescription"
        NOTE = "note", "Clinical Note"
        SYSTEM = "system", "System Event"

    session = models.ForeignKey("TelemedicineSession", on_delete=models.CASCADE, related_name="interactions")
    sender = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, related_name="sent_interactions")
    interaction_type = models.CharField(max_length=15, choices=InteractionType.choices)
    content = models.TextField(blank=True)
    file_url = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict)
    is_encrypted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "telemedicine_interactions"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["sender", "interaction_type"]),
        ]

    def __str__(self):
        return f"{self.get_interaction_type_display()} - Session {self.session_id}"


# ─── Public Health Forecast ───
class PublicHealthForecast(models.Model):
    class ForecastCategory(models.TextChoices):
        DISEASE = "disease", "Disease Forecast"
        MORTALITY = "mortality", "Mortality Forecast"
        DEMAND = "demand", "Healthcare Demand Forecast"
        VACCINATION = "vaccination", "Vaccination Coverage Forecast"
        OUTBREAK = "outbreak", "Outbreak Trajectory"

    forecast_category = models.CharField(max_length=15, choices=ForecastCategory.choices, db_index=True)
    county = models.CharField(max_length=100, db_index=True)
    disease_code = models.CharField(max_length=20, blank=True, db_index=True)
    disease_name = models.CharField(max_length=200, blank=True)
    forecast_date = models.DateField(db_index=True)
    predicted_cases = models.FloatField()
    predicted_lower = models.FloatField(null=True, blank=True)
    predicted_upper = models.FloatField(null=True, blank=True)
    confidence_level = models.FloatField(default=0.95)
    model_name = models.CharField(max_length=200, blank=True)
    seasonality_factor = models.FloatField(default=1.0)
    trend_direction = models.CharField(max_length=10, blank=True, choices=[
        ("increasing", "Increasing"), ("decreasing", "Decreasing"), ("stable", "Stable"),
    ])
    risk_level = models.CharField(max_length=10, default="low", choices=[
        ("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("critical", "Critical"),
    ])
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "public_health_forecasts"
        ordering = ["-forecast_date"]
        indexes = [
            models.Index(fields=["county", "forecast_category", "forecast_date"]),
            models.Index(fields=["disease_code", "forecast_date"]),
            models.Index(fields=["risk_level"]),
        ]

    def __str__(self):
        return f"{self.get_forecast_category_display()}: {self.predicted_cases} ({self.county})"


# ─── Infrastructure Event (Autonomous Ops) ───
class InfrastructureEvent(models.Model):
    class EventType(models.TextChoices):
        SCALING = "scaling", "Auto Scaling Event"
        HEALTH_CHECK = "health_check", "Health Check"
        ALERT = "alert", "Infrastructure Alert"
        RECOVERY = "recovery", "Auto Recovery"
        CONFIG = "config", "Configuration Change"
        DEPLOYMENT = "deployment", "Deployment Event"
        PERFORMANCE = "performance", "Performance Anomaly"

    event_type = models.CharField(max_length=20, choices=EventType.choices, db_index=True)
    severity = models.CharField(max_length=10, default="info", choices=[
        ("info", "Info"), ("warning", "Warning"), ("error", "Error"), ("critical", "Critical"),
    ])
    service_name = models.CharField(max_length=200, blank=True)
    host_name = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    metric_data = models.JSONField(default=dict)
    auto_action_taken = models.CharField(max_length=500, blank=True)
    auto_action_success = models.BooleanField(null=True, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "infrastructure_events"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["event_type", "severity"]),
            models.Index(fields=["service_name", "occurred_at"]),
            models.Index(fields=["occurred_at"]),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.event_type} - {self.service_name}"


# ═══════════════════════════════════════════════════════════════
# Phase 8: National Intelligent Healthcare Ecosystem
# ═══════════════════════════════════════════════════════════════


# ─── Emergency Response Event ───
class EmergencyResponseEvent(models.Model):
    class EmergencyType(models.TextChoices):
        NATURAL_DISASTER = "natural_disaster", "Natural Disaster"
        PANDEMIC = "pandemic", "Pandemic Outbreak"
        MASS_CASUALTY = "mass_casualty", "Mass Casualty Incident"
        TERRORISM = "terrorism", "Terrorism Event"
        INFRASTRUCTURE = "infrastructure", "Infrastructure Failure"
        OTHER = "other", "Other Emergency"

    class Severity(models.TextChoices):
        LEVEL_1 = "level_1", "Level 1 - Minor"
        LEVEL_2 = "level_2", "Level 2 - Moderate"
        LEVEL_3 = "level_3", "Level 3 - Serious"
        LEVEL_4 = "level_4", "Level 4 - Critical"
        LEVEL_5 = "level_5", "Level 5 - Catastrophic"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RESPONDING = "responding", "Responding"
        CONTAINED = "contained", "Contained"
        RESOLVED = "resolved", "Resolved"
        AFTERMATH = "aftermath", "Aftermath"

    emergency_type = models.CharField(max_length=20, choices=EmergencyType.choices, db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.LEVEL_1)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    title = models.CharField(max_length=300)
    description = models.TextField()
    location_region = models.CharField(max_length=200, blank=True, db_index=True)
    affected_counties = models.JSONField(default=list)
    affected_population = models.IntegerField(default=0)
    estimated_casualties = models.IntegerField(default=0)
    hospital_capacity_impact = models.JSONField(default=dict)
    resource_needs = models.JSONField(default=dict)
    responding_units = models.JSONField(default=list)
    coordination_center = models.CharField(max_length=200, blank=True)
    incident_commander = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="commanded_incidents")
    escalated_at = models.DateTimeField(null=True, blank=True)
    contained_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    lessons_learned = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "emergency_response_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["emergency_type", "severity"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["location_region", "emergency_type"]),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.title} - {self.get_status_display()}"


# ─── Predictive Forecast (Enhanced) ───
class PredictiveForecast(models.Model):
    class ForecastDomain(models.TextChoices):
        DISEASE = "disease", "Disease Incidence"
        MORTALITY = "mortality", "Mortality Rate"
        DEMAND = "demand", "Healthcare Demand"
        CAPACITY = "capacity", "Hospital Capacity"
        STAFFING = "staffing", "Staffing Need"
        EQUIPMENT = "equipment", "Equipment Utilization"
        FINANCIAL = "financial", "Financial Forecast"
        EMERGENCY = "emergency", "Emergency Volume"

    domain = models.CharField(max_length=15, choices=ForecastDomain.choices, db_index=True)
    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, null=True, blank=True, related_name="forecasts")
    county = models.CharField(max_length=100, blank=True, db_index=True)
    region = models.CharField(max_length=200, blank=True)
    metric_name = models.CharField(max_length=200)
    predicted_value = models.FloatField()
    actual_value = models.FloatField(null=True, blank=True)
    predicted_lower = models.FloatField(null=True, blank=True)
    predicted_upper = models.FloatField(null=True, blank=True)
    confidence_level = models.FloatField(default=0.95)
    forecast_date = models.DateField(db_index=True)
    forecast_horizon_days = models.IntegerField(default=7)
    trend_direction = models.CharField(max_length=15, blank=True, choices=[
        ("increasing", "Increasing"), ("decreasing", "Decreasing"), ("stable", "Stable"),
    ])
    seasonality_factor = models.FloatField(default=1.0)
    model_name = models.CharField(max_length=200, blank=True)
    model_accuracy = models.FloatField(null=True, blank=True)
    features_used = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "predictive_forecasts"
        ordering = ["-forecast_date"]
        indexes = [
            models.Index(fields=["domain", "forecast_date"]),
            models.Index(fields=["hospital", "domain"]),
            models.Index(fields=["county", "domain", "forecast_date"]),
            models.Index(fields=["region", "domain"]),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.predicted_value} ({self.forecast_date})"


# ─── Infrastructure Twin (Digital Twin) ───
class InfrastructureTwin(models.Model):
    class TwinType(models.TextChoices):
        HOSPITAL = "hospital", "Hospital Operational Twin"
        REGIONAL = "regional", "Regional Healthcare Twin"
        EMERGENCY = "emergency", "Emergency Response Twin"
        POPULATION = "population", "Population Health Twin"
        EQUIPMENT = "equipment", "Equipment Fleet Twin"

    class SimulationStatus(models.TextChoices):
        IDLE = "idle", "Idle"
        RUNNING = "running", "Simulation Running"
        COMPLETED = "completed", "Simulation Completed"
        FAILED = "failed", "Simulation Failed"

    twin_type = models.CharField(max_length=15, choices=TwinType.choices, db_index=True)
    name = models.CharField(max_length=300)
    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, null=True, blank=True, related_name="digital_twins")
    region = models.CharField(max_length=200, blank=True, db_index=True)
    description = models.TextField(blank=True)
    simulation_status = models.CharField(max_length=10, choices=SimulationStatus.choices, default=SimulationStatus.IDLE)
    current_parameters = models.JSONField(default=dict)
    simulation_results = models.JSONField(default=dict)
    baseline_metrics = models.JSONField(default=dict)
    predictive_scenarios = models.JSONField(default=list)
    last_simulated_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "infrastructure_twins"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["twin_type", "is_active"]),
            models.Index(fields=["hospital", "twin_type"]),
            models.Index(fields=["region", "twin_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_twin_type_display()})"


# ─── AI Model Registry ───
class AIModelRegistry(models.Model):
    class ModelStatus(models.TextChoices):
        DEV = "development", "In Development"
        TESTING = "testing", "Testing"
        STAGING = "staging", "Staging"
        PRODUCTION = "production", "Production"
        DEPRECATED = "deprecated", "Deprecated"
        RETIRED = "retired", "Retired"

    model_name = models.CharField(max_length=300)
    model_version = models.CharField(max_length=50)
    model_type = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=ModelStatus.choices, default=ModelStatus.DEV)
    model_artifact_path = models.CharField(max_length=500, blank=True)
    input_schema = models.JSONField(default=dict)
    output_schema = models.JSONField(default=dict)
    performance_metrics = models.JSONField(default=dict)
    explainability_config = models.JSONField(default=dict)
    governance_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_models")
    approved_at = models.DateTimeField(null=True, blank=True)
    audit_trail = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_model_registry"
        unique_together = [["model_name", "model_version"]]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model_type", "status"]),
            models.Index(fields=["status", "is_active"]),
        ]

    def __str__(self):
        return f"{self.model_name} v{self.model_version} ({self.get_status_display()})"


# ─── Smart Hospital Metric ───
class SmartHospitalMetric(models.Model):
    class MetricCategory(models.TextChoices):
        OCCUPANCY = "occupancy", "Bed Occupancy"
        ENERGY = "energy", "Energy Consumption"
        EQUIPMENT = "equipment", "Equipment Status"
        STAFF = "staff", "Staff Utilization"
        PATIENT_FLOW = "patient_flow", "Patient Flow"
        OPERATIONAL = "operational", "Operational Efficiency"
        MAINTENANCE = "maintenance", "Maintenance Needs"

    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, related_name="smart_metrics")
    ward = models.ForeignKey("Ward", on_delete=models.SET_NULL, null=True, blank=True)
    metric_category = models.CharField(max_length=15, choices=MetricCategory.choices, db_index=True)
    metric_name = models.CharField(max_length=200)
    metric_value = models.FloatField()
    unit = models.CharField(max_length=50, blank=True)
    threshold_warning = models.FloatField(null=True, blank=True)
    threshold_critical = models.FloatField(null=True, blank=True)
    is_alert = models.BooleanField(default=False)
    recorded_at = models.DateTimeField(db_index=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "smart_hospital_metrics"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["hospital", "metric_category", "recorded_at"]),
            models.Index(fields=["metric_category", "is_alert"]),
            models.Index(fields=["ward", "metric_category"]),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.unit}"


# ─── Population Health Insight ───
class PopulationHealthInsight(models.Model):
    class InsightCategory(models.TextChoices):
        DISEASE_BURDEN = "disease_burden", "Disease Burden"
        HEALTHCARE_ACCESS = "healthcare_access", "Healthcare Access"
        RISK_FACTOR = "risk_factor", "Risk Factor Prevalence"
        PREVENTIVE = "preventive", "Preventive Care"
        SOCIAL_DETERMINANT = "social_determinant", "Social Determinant"
        HEALTH_EQUITY = "health_equity", "Health Equity"

    category = models.CharField(max_length=20, choices=InsightCategory.choices, db_index=True)
    county = models.CharField(max_length=100, db_index=True)
    sub_county = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=200, blank=True)
    indicator_name = models.CharField(max_length=300)
    indicator_value = models.FloatField()
    population_base = models.IntegerField(default=0)
    confidence_interval_low = models.FloatField(null=True, blank=True)
    confidence_interval_high = models.FloatField(null=True, blank=True)
    percentile_rank = models.FloatField(null=True, blank=True)
    trend_direction = models.CharField(max_length=15, blank=True)
    comparison_national = models.FloatField(null=True, blank=True)
    comparison_regional = models.FloatField(null=True, blank=True)
    period_start = models.DateField()
    period_end = models.DateField()
    metadata = models.JSONField(default=dict)
    is_anonymized = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "population_health_insights"
        ordering = ["-period_end"]
        indexes = [
            models.Index(fields=["category", "county", "period_end"]),
            models.Index(fields=["county", "category"]),
            models.Index(fields=["region", "category"]),
        ]

    def __str__(self):
        return f"{self.indicator_name}: {self.indicator_value} ({self.county})"


# ─── Operational Alert ───
class OperationalAlert(models.Model):
    class AlertCategory(models.TextChoices):
        CAPACITY = "capacity", "Capacity Alert"
        EQUIPMENT = "equipment", "Equipment Alert"
        STAFF = "staff", "Staff Alert"
        PERFORMANCE = "performance", "Performance Alert"
        SECURITY = "security", "Security Alert"
        INFRASTRUCTURE = "infrastructure", "Infrastructure Alert"
        ANOMALY = "anomaly", "System Anomaly"

    class AlertSeverity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"
        EMERGENCY = "emergency", "Emergency"

    category = models.CharField(max_length=15, choices=AlertCategory.choices, db_index=True)
    severity = models.CharField(max_length=10, choices=AlertSeverity.choices, default=AlertSeverity.INFO)
    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, null=True, blank=True, related_name="operational_alerts")
    title = models.CharField(max_length=300)
    description = models.TextField()
    metric_name = models.CharField(max_length=200, blank=True)
    metric_value = models.FloatField(null=True, blank=True)
    threshold_value = models.FloatField(null=True, blank=True)
    source_service = models.CharField(max_length=200, blank=True)
    recommended_action = models.TextField(blank=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="acknowledged_alerts")
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "operational_alerts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "severity"]),
            models.Index(fields=["hospital", "created_at"]),
            models.Index(fields=["severity", "is_resolved"]),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.title}"


# ─── Device Telemetry Event ───
class DeviceTelemetryEvent(models.Model):
    class TelemetryType(models.TextChoices):
        VITAL = "vital", "Patient Vital"
        ENVIRONMENTAL = "environmental", "Environmental Reading"
        LOCATION = "location", "Location Data"
        STATUS = "status", "Device Status"
        DIAGNOSTIC = "diagnostic", "Device Diagnostic"
        ALERT = "alert", "Device Alert"

    device = models.ForeignKey("SmartHospitalDevice", on_delete=models.CASCADE, related_name="telemetry_events")
    hospital = models.ForeignKey("Hospital", on_delete=models.CASCADE, related_name="telemetry_events")
    telemetry_type = models.CharField(max_length=15, choices=TelemetryType.choices, db_index=True)
    metric_name = models.CharField(max_length=200)
    metric_value = models.FloatField()
    unit = models.CharField(max_length=50, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    signal_strength = models.FloatField(null=True, blank=True)
    battery_level = models.FloatField(null=True, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)
    payload = models.JSONField(default=dict)
    is_abnormal = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    recorded_at = models.DateTimeField(db_index=True)
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "device_telemetry_events"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["device", "recorded_at"]),
            models.Index(fields=["hospital", "telemetry_type", "recorded_at"]),
            models.Index(fields=["telemetry_type", "is_abnormal"]),
            models.Index(fields=["recorded_at"]),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.unit} ({self.device_id})"


class LoginAttempt(models.Model):
    """Audit record of each login attempt for threat intelligence."""

    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_successful = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "login_attempts"
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(fields=["ip_address", "is_successful"]),
            models.Index(fields=["user", "attempted_at"]),
        ]

    def __str__(self):
        return f"Login attempt by {self.user_id or 'anonymous'} at {self.attempted_at}"


class EventStreamLog(models.Model):
    """Event-stream log for the event-driven architecture."""

    event_id = models.UUIDField(unique=True, editable=False)
    event_source = models.CharField(max_length=100, db_index=True)
    event_type = models.CharField(max_length=200, db_index=True)
    event_version = models.CharField(max_length=10, default="1.0")
    aggregate_type = models.CharField(max_length=100, blank=True)
    aggregate_id = models.CharField(max_length=100, blank=True)
    data = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    correlation_id = models.CharField(max_length=100, blank=True, db_index=True)
    causation_id = models.CharField(max_length=100, blank=True)
    occurred_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "event_stream_log"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["event_source", "occurred_at"]),
            models.Index(fields=["correlation_id", "occurred_at"]),
            models.Index(fields=["aggregate_type", "aggregate_id"]),
            models.Index(fields=["event_type", "occurred_at"]),
        ]

    def __str__(self):
        return f"{self.event_source}.{self.event_type} [{self.event_id}]"


class TelemedicineRecording(models.Model):
    """Recording of a telemedicine session."""

    session = models.ForeignKey("TelemedicineSession", on_delete=models.CASCADE, related_name="recordings")
    recording_type = models.CharField(max_length=50)
    file_url = models.URLField(max_length=500, blank=True)
    duration_seconds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "telemedicine_recordings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Recording {self.recording_type} for session {self.session_id}"
