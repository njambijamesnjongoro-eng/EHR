export type UserRole =
  | "super_admin"
  | "hospital_admin"
  | "doctor"
  | "nurse"
  | "lab_technician"
  | "pharmacist"
  | "receptionist"
  | "patient";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  phone_number: string;
  is_active: boolean;
  hospital_id?: number;
  national_health_id?: string;
  created_at: string;
}

export interface Patient {
  id: number;
  health_id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  national_id: string;
  date_of_birth: string;
  age: number;
  gender: "male" | "female" | "other";
  phone_number: string;
  email: string;
  address: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  blood_group: string;
  allergies: string;
  chronic_conditions: string;
  qr_code: string;
  created_at: string;
  updated_at: string;
}

export interface PatientHistory {
  id: number;
  patient: number;
  record_type: string;
  title: string;
  description: string;
  recorded_by: number;
  recorded_by_name: string;
  recorded_at: string;
  is_confidential: boolean;
  metadata: Record<string, unknown>;
}

export interface AuditLogEntry {
  id: number;
  user: number;
  user_name: string;
  action: string;
  resource_type: string;
  resource_id: string;
  description: string;
  ip_address: string;
  request_path: string;
  response_status: number;
  created_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  count?: number;
  total_pages?: number;
  current_page?: number;
  page_size?: number;
  next?: string;
  previous?: string;
  results?: T[];
  errors?: Record<string, string[]>;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface PatientFormData {
  first_name: string;
  last_name: string;
  national_id: string;
  date_of_birth: string;
  gender: "male" | "female" | "other";
  phone_number: string;
  email: string;
  address: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  blood_group: string;
  allergies: string;
  chronic_conditions: string;
}

// ─── Phase 2: Clinical Types ───

export type VisitStatus = "in_progress" | "completed" | "cancelled" | "follow_up";

export interface Visit {
  id: number;
  patient: number;
  patient_name: string;
  doctor: number;
  doctor_name: string;
  visit_date: string;
  chief_complaint: string;
  symptoms: string;
  diagnosis_summary: string;
  treatment_plan: string;
  follow_up_date: string | null;
  status: VisitStatus;
  notes: string;
  diagnoses?: Diagnosis[];
  prescriptions?: Prescription[];
  vital_signs?: VitalSignRecord[];
  created_at: string;
  updated_at: string;
}

export interface VisitFormData {
  patient: number;
  chief_complaint: string;
  symptoms: string;
  diagnosis_summary: string;
  treatment_plan: string;
  follow_up_date: string;
  notes: string;
}

export interface VitalSignRecord {
  id: number;
  visit: number;
  patient: number;
  temperature: string | null;
  blood_pressure_systolic: number | null;
  blood_pressure_diastolic: number | null;
  pulse_rate: number | null;
  respiratory_rate: number | null;
  oxygen_saturation: string | null;
  weight: string | null;
  height: string | null;
  bmi: string | null;
  notes: string;
  recorded_by: number | null;
  recorded_by_name: string | null;
  recorded_at: string;
}

export interface VitalSignFormData {
  visit: number;
  patient: number;
  temperature: string;
  blood_pressure_systolic: string;
  blood_pressure_diastolic: string;
  pulse_rate: string;
  respiratory_rate: string;
  oxygen_saturation: string;
  weight: string;
  height: string;
  notes: string;
}

export type Severity = "mild" | "moderate" | "severe" | "critical";

export interface Diagnosis {
  id: number;
  visit: number;
  patient: number;
  diagnosis_type: "primary" | "secondary";
  diagnosis_name: string;
  icd_code: string;
  severity: Severity;
  clinical_notes: string;
  is_confirmed: boolean;
  diagnosed_by: number;
  diagnosed_by_name: string;
  diagnosed_at: string;
  created_at: string;
}

export interface DiagnosisFormData {
  visit: number;
  patient: number;
  diagnosis_type: "primary" | "secondary";
  diagnosis_name: string;
  icd_code: string;
  severity: Severity;
  clinical_notes: string;
  is_confirmed: boolean;
}

export type Frequency = "od" | "bd" | "tds" | "qid" | "qhs" | "prn" | "stat";
export type Route = "oral" | "iv" | "im" | "sc" | "topical" | "inhalation" | "sublingual" | "rectal" | "ophthalmic" | "otic";

export interface Prescription {
  id: number;
  visit: number;
  patient: number;
  medication_name: string;
  dosage: string;
  frequency: Frequency;
  duration_days: number | null;
  duration_text: string;
  route: Route;
  instructions: string;
  prescribed_by: number;
  prescribed_by_name: string;
  prescribed_at: string;
  is_dispensed: boolean;
  dispensed_at: string | null;
  dispensed_by: number | null;
  dispensed_by_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface PrescriptionFormData {
  visit: number;
  patient: number;
  medication_name: string;
  dosage: string;
  frequency: Frequency;
  duration_days: number;
  duration_text: string;
  route: Route;
  instructions: string;
}

export type LabPriority = "routine" | "urgent" | "stat";
export type LabStatus = "requested" | "sample_collected" | "in_progress" | "completed" | "cancelled";

export interface LabRequest {
  id: number;
  visit: number;
  patient: number;
  patient_name: string;
  test_name: string;
  priority: LabPriority;
  status: LabStatus;
  clinical_notes: string;
  requested_by: number;
  requested_by_name: string;
  requested_at: string;
  created_at: string;
}

export interface LabRequestFormData {
  visit: number;
  patient: number;
  test_name: string;
  priority: LabPriority;
  clinical_notes: string;
}

export interface LabResult {
  id: number;
  lab_request: number;
  test_name: string;
  patient: number;
  result_data: Record<string, unknown>;
  result_text: string;
  remarks: string;
  is_abnormal: boolean;
  file_attachment: string | null;
  performed_by: number;
  performed_by_name: string;
  result_at: string;
  created_at: string;
}

export interface TimelineEvent {
  type: "visit" | "diagnosis" | "prescription" | "lab_request" | "lab_result";
  id: number;
  title: string;
  description: string;
  date: string;
  sort_date: string;
  visit_id: number;
  status?: string;
  extra?: Record<string, unknown>;
}

// ─── Phase 3: Admissions ───

export type WardType = "general" | "private" | "icu" | "pediatrics" | "maternity" | "surgery" | "isolation";
export type BedStatus = "available" | "occupied" | "maintenance";
export type AdmissionStatus = "active" | "discharged" | "transferred";

export interface Ward {
  id: number;
  ward_name: string;
  ward_type: WardType;
  capacity: number;
  available_beds: number;
  occupied_beds: number;
  total_beds: number;
  description: string;
  is_active: boolean;
}

export interface Bed {
  id: number;
  ward: number;
  ward_name: string;
  bed_number: string;
  occupancy_status: BedStatus;
}

export interface Admission {
  id: number;
  patient: number;
  patient_name: string;
  patient_health_id: string;
  ward: number | null;
  ward_name: string;
  bed: number | null;
  bed_number: string;
  admission_reason: string;
  admission_date: string;
  discharge_date: string | null;
  status: AdmissionStatus;
  admitted_by: number | null;
  admitted_by_name: string;
  discharge_notes: string;
}

// ─── Phase 3: Billing ───

export type InvoiceStatus = "pending" | "paid" | "partially_paid" | "cancelled";
export type PaymentMethod = "cash" | "card" | "mpesa" | "insurance" | "bank_transfer";

export interface Invoice {
  id: number;
  invoice_number: string;
  patient: number;
  patient_name: string;
  patient_health_id: string;
  visit: number | null;
  admission: number | null;
  consultation_fee: string;
  lab_fee: string;
  pharmacy_fee: string;
  admission_fee: string;
  radiology_fee: string;
  other_fees: string;
  discount: string;
  tax: string;
  total_amount: string;
  amount_paid: string;
  balance: string;
  status: InvoiceStatus;
  insurance_provider: string;
  insurance_policy_no: string;
  notes: string;
  payments?: PaymentRecord[];
  created_at: string;
  updated_at: string;
}

export interface InvoiceFormData {
  patient: number;
  visit?: number;
  admission?: number;
  consultation_fee: string;
  lab_fee: string;
  pharmacy_fee: string;
  admission_fee: string;
  radiology_fee: string;
  other_fees: string;
  discount: string;
  tax: string;
  insurance_provider: string;
  insurance_policy_no: string;
  notes: string;
}

export interface PaymentRecord {
  id: number;
  invoice: number;
  amount_paid: string;
  payment_method: PaymentMethod;
  transaction_reference: string;
  payment_date: string;
  received_by: number;
  received_by_name: string;
  notes: string;
  created_at: string;
}

// ─── Phase 3: Imaging ───

export type ImagingType = "xray" | "mri" | "ct_scan" | "ultrasound" | "mammography" | "pet_scan";
export type ImagingPriority = "routine" | "urgent" | "stat";
export type ImagingStatus = "requested" | "scheduled" | "completed" | "cancelled";

export interface ImagingRequest {
  id: number;
  visit: number;
  patient: number;
  patient_name: string;
  imaging_type: ImagingType;
  priority: ImagingPriority;
  status: ImagingStatus;
  clinical_history: string;
  region_examined: string;
  requested_by: number;
  requested_by_name: string;
  requested_at: string;
  created_at: string;
}

export interface ImagingResult {
  id: number;
  imaging_request: number;
  imaging_type: string;
  patient: number;
  findings: string;
  impression: string;
  report: string;
  radiologist: number;
  radiologist_name: string;
  image_file: string | null;
  report_file: string | null;
  is_abnormal: boolean;
  result_at: string;
  created_at: string;
}

// ─── Phase 3: Notifications ───

export type NotificationCategory = "lab_result" | "imaging" | "admission" | "billing" | "appointment" | "general";

export interface Notification {
  id: number;
  recipient: number;
  patient: number | null;
  category: NotificationCategory;
  title: string;
  message: string;
  is_read: boolean;
  link: string;
  created_at: string;
}

// ─── Phase 3: Reports ───

export interface DashboardStats {
  active_admissions: number;
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  total_patients: number;
  total_visits: number;
  today_visits: number;
  monthly_revenue: number;
  pending_invoices: number;
  pending_labs: number;
  pending_imaging: number;
  ward_stats: { ward_name: string; ward_type: string; total_beds: number; occ_beds: number }[];
}

// ─── Phase 4: Multi-Hospital ───

export type HospitalType = "national_referral" | "county_referral" | "county" | "sub_county" | "private" | "mission" | "clinic";

export interface Hospital {
  id: number;
  hospital_name: string;
  hospital_code: string;
  hospital_type: HospitalType;
  county: string;
  sub_county: string;
  address: string;
  phone_number: string;
  email: string;
  license_number: string;
  is_active: boolean;
  metadata: Record<string, unknown>;
  staff_count: number;
  department_count: number;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: number;
  hospital: number;
  department_name: string;
  department_code: string;
  description: string;
  is_active: boolean;
}

export interface HospitalStaff {
  id: number;
  user: number;
  user_email: string;
  user_name: string;
  hospital: number;
  hospital_name: string;
  department: number | null;
  department_name: string;
  staff_role: string;
  employee_id: string;
  is_active: boolean;
}

// ─── Phase 4: Referrals ───

export type ReferralPriority = "routine" | "urgent" | "emergency";
export type ReferralStatus = "pending" | "accepted" | "declined" | "completed" | "cancelled";

export interface Referral {
  id: number;
  patient: number;
  patient_name: string;
  patient_health_id: string;
  referring_hospital: number;
  referring_hospital_name: string;
  referring_doctor: number;
  referring_doctor_name: string;
  receiving_hospital: number;
  receiving_hospital_name: string;
  receiving_department: number | null;
  department_name: string;
  priority: ReferralPriority;
  status: ReferralStatus;
  clinical_summary: string;
  reason_for_referral: string;
  referral_notes: string;
  response_notes: string;
  responded_by: number | null;
  responded_at: string | null;
  completed_at: string | null;
  created_at: string;
}

// ─── Phase 4: Sync ───

export interface SyncStatus {
  pending_count: number;
  failed_count: number;
  last_sync: string | null;
}

export interface SyncQueueItem {
  id: number;
  hospital: number;
  resource_type: string;
  resource_id: string;
  action: "create" | "update" | "delete";
  status: "pending" | "processing" | "completed" | "failed" | "conflict";
  error_message: string;
  retry_count: number;
  client_timestamp: string;
}

// ─── Phase 4: Analytics ───

export interface HospitalDashboardData {
  period_days: number;
  total_patients: number;
  new_patients: number;
  total_visits: number;
  daily_avg_visits: number;
  active_admissions: number;
  admissions_period: number;
  total_revenue: number;
  total_collected: number;
  outstanding: number;
  top_diagnoses: { diagnosis_name: string; count: number }[];
}

export interface RevenueMonthly {
  month: string;
  total: number;
  collected: number;
  count: number;
}

export interface NationalAggregate {
  total_hospitals: number;
  total_patients: number;
  total_visits: number;
  total_referrals: number;
  active_admissions: number;
  hospitals_by_county: { county: string; count: number }[];
}

// ─── Phase 4: Insurance ───

export type InsuranceProvider = "sha" | "nhif" | "private" | "community";
export type ClaimStatus = "draft" | "submitted" | "pending" | "approved" | "rejected" | "paid";

export interface InsuranceProfile {
  id: number;
  patient: number;
  patient_name: string;
  patient_health_id: string;
  provider: InsuranceProvider;
  policy_number: string;
  member_number: string;
  coverage_type: string;
  is_active: boolean;
  verified: boolean;
  coverage_limit: string;
  deductible: string;
  effective_from: string;
  effective_to: string | null;
}

export interface InsuranceClaim {
  id: number;
  insurance_profile: number;
  patient_name: string;
  policy_number: string;
  claim_number: string;
  status: ClaimStatus;
  total_amount: string;
  approved_amount: string;
  notes: string;
  submitted_at: string | null;
  created_at: string;
}

// ─── Phase 4: Telemedicine ───

export type TelemedStatus = "scheduled" | "in_progress" | "completed" | "cancelled" | "missed";

export interface TelemedicineSession {
  id: number;
  patient: number;
  patient_name: string;
  patient_health_id: string;
  doctor: number;
  doctor_name: string;
  hospital: number;
  hospital_name: string;
  scheduled_at: string;
  started_at: string | null;
  ended_at: string | null;
  status: TelemedStatus;
  session_type: "video" | "audio" | "chat";
  consultation_notes: string;
  meeting_url: string;
}

// ─── Phase 5: Security ───

export type SecurityCategory =
  | "login_attempt" | "suspicious_activity" | "anomaly"
  | "intrusion" | "policy_violation" | "rate_limit"
  | "auth_failure" | "token_anomaly";

export type SecuritySeverity = "info" | "low" | "medium" | "high" | "critical";

export interface SecurityEvent {
  id: number;
  category: SecurityCategory;
  severity: SecuritySeverity;
  user: number | null;
  user_email: string;
  hospital: number | null;
  ip_address: string | null;
  user_agent: string;
  device_fingerprint: string;
  risk_score: number;
  description: string;
  metadata: Record<string, unknown>;
  detected_at: string;
  resolved: boolean;
  resolved_by: number | null;
  resolved_at: string | null;
}

export interface DeviceFingerprint {
  id: number;
  user: number;
  fingerprint_hash: string;
  device_name: string;
  device_type: string;
  os: string;
  browser: string;
  ip_address: string | null;
  is_trusted: boolean;
  last_seen_at: string;
  first_seen_at: string;
  risk_count: number;
}

export interface MFAToken {
  id: number;
  user: number;
  token_type: "totp" | "email" | "sms" | "backup";
  secret: string;
  is_active: boolean;
  verified_at: string | null;
  created_at: string;
}

export interface RiskDashboard {
  total_high_risk: number;
  critical_events_24h: number;
  unique_users_flagged: number;
  recent_unresolved: SecurityEvent[];
}

// ─── Phase 5: Monitoring ───

export type MetricType =
  | "api_latency" | "db_query_time" | "cache_hit_ratio"
  | "queue_depth" | "cpu_usage" | "memory_usage"
  | "disk_usage" | "active_users" | "api_requests"
  | "error_rate" | "sync_lag";

export interface SystemHealthMetric {
  id: number;
  metric_type: MetricType;
  hospital: number | null;
  value: number;
  unit: string;
  tags: Record<string, string>;
  recorded_at: string;
}

export interface SystemHealthDashboard {
  queue_depth: number;
  active_users: number;
  cache_hit_ratio: number;
  recent_latency_avg: number;
  error_rate_24h: number;
  recent_metrics: SystemHealthMetric[];
}

// ─── Phase 5: Compliance ───

export type ConsentType =
  | "data_processing" | "data_sharing" | "research"
  | "marketing" | "telemedicine";

export type ConsentStatus = "granted" | "revoked" | "expired";

export interface ConsentLog {
  id: number;
  patient: number;
  patient_name: string;
  consent_type: ConsentType;
  status: ConsentStatus;
  granted_by: number;
  granted_by_name: string;
  granted_at: string;
  expires_at: string | null;
  revoked_at: string | null;
  revocation_reason: string;
  consent_version: string;
  metadata: Record<string, unknown>;
}

export type EnterpriseAuditEventType =
  | "data_access" | "security" | "admin" | "system" | "integration" | "sync";

export interface EnterpriseAuditEvent {
  id: number;
  event_type: EnterpriseAuditEventType;
  hospital: number | null;
  user: number | null;
  user_name: string;
  actor_type: "user" | "system" | "api" | "integration";
  resource_type: string;
  resource_id: string;
  action: string;
  description: string;
  ip_address: string | null;
  user_agent: string;
  metadata: Record<string, unknown>;
  severity: "info" | "warning" | "error" | "critical";
  created_at: string;
}

export interface AuditReport {
  period_days: number;
  total_events: number;
  by_event_type: Record<string, number>;
  by_severity: Record<string, number>;
  by_user: Record<string, number>;
  security_events: number;
}

// ─── Phase 5: Interop ───

export type ExternalSystemType =
  | "fhir" | "hl7" | "insurance" | "lab" | "pharmacy"
  | "government" | "mobile" | "other";

export interface ExternalSystem {
  id: number;
  system_name: string;
  system_type: ExternalSystemType;
  hospital: number | null;
  base_url: string;
  api_key_hash: string;
  auth_type: "api_key" | "oauth2" | "basic" | "mutual_tls" | "none";
  is_active: boolean;
  config: Record<string, unknown>;
  last_sync_at: string | null;
  last_sync_status: string;
  created_at: string;
  updated_at: string;
}

// ─── Phase 6: AI Assist ───

export type AIInsightType =
  | "risk_assessment" | "diagnosis_suggestion" | "medication_check"
  | "deterioration_alert" | "treatment_recommendation"
  | "anomaly_detection" | "clinical_summary";

export type AIConfidence = "low" | "medium" | "high";

export interface AIInsight {
  id: number;
  insight_type: AIInsightType;
  patient: number | null;
  patient_name: string;
  visit: number | null;
  title: string;
  summary: string;
  details: Record<string, unknown>;
  confidence: AIConfidence;
  confidence_score: number;
  source_service: string;
  is_reviewed: boolean;
  reviewed_by: number | null;
  reviewed_by_name: string;
  reviewed_at: string | null;
  clinical_action_taken: string;
  created_at: string;
}

// ─── Phase 6: Wearable & IoT ───

export type WearableDeviceType =
  | "smartwatch" | "fitness_band" | "glucose_monitor"
  | "blood_pressure" | "heart_rate" | "pulse_oximeter"
  | "ecg" | "other";

export type ReadingType =
  | "heart_rate" | "blood_pressure" | "oxygen_saturation"
  | "glucose" | "temperature" | "steps" | "calories"
  | "sleep" | "ecg" | "weight" | "fall" | "location" | "other";

export interface WearableDevice {
  id: number;
  patient: number;
  device_type: WearableDeviceType;
  device_name: string;
  manufacturer: string;
  model_number: string;
  serial_number: string;
  firmware_version: string;
  is_active: boolean;
  is_verified: boolean;
  pairing_token: string;
  config: Record<string, unknown>;
  last_sync_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DeviceReading {
  id: number;
  device: number;
  patient: number;
  reading_type: ReadingType;
  value: number;
  unit: string;
  metadata: Record<string, unknown>;
  recorded_at: string;
  ingested_at: string;
  is_abnormal: boolean;
}

// ─── Phase 6: Biometric ───

export type BiometricType = "fingerprint" | "face" | "iris";

export interface BiometricIdentity {
  id: number;
  user: number;
  biometric_type: BiometricType;
  biometric_hash: string;
  encrypted_template: string;
  is_active: boolean;
  verified_at: string | null;
  device_id: string;
  fail_count: number;
  created_at: string;
  updated_at: string;
}

// ─── Phase 6: Public Health ───

export interface PublicHealthMetric {
  id: number;
  metric_category: string;
  county: string;
  sub_county: string;
  disease_code: string;
  disease_name: string;
  metric_value: number;
  metric_unit: string;
  population_base: number;
  sample_size: number;
  confidence_interval_low: number | null;
  confidence_interval_high: number | null;
  period_start: string;
  period_end: string;
  created_at: string;
}

export interface OutbreakSignal {
  icd_code: string;
  diagnosis_name: string;
  recent_count: number;
  baseline_count: number;
  ratio: number;
  signal_strength: string;
}

// ─── Phase 6: Predictive ───

export type AlertCategory =
  | "patient_deterioration" | "hospital_overload" | "equipment_failure"
  | "epidemic_warning" | "resource_shortage" | "anomaly" | "bed_crisis";

export type AlertSeverity = "info" | "warning" | "critical" | "emergency";

export interface PredictiveAlert {
  id: number;
  category: AlertCategory;
  severity: AlertSeverity;
  title: string;
  description: string;
  confidence_score: number;
  predicted_at: string;
  status: string;
}

export interface HospitalLoadPrediction {
  hospital_id: number;
  current_occupancy: number;
  total_beds: number;
  bed_utilization_pct: number;
  avg_daily_admissions: number;
  predicted_occupancy_in_days: Record<string, number>;
  risk_level: string;
}

// ─── Phase 6: Smart Hospital ───

export interface SmartHospitalDevice {
  id: number;
  hospital: number;
  hospital_name: string;
  ward: number | null;
  ward_name: string;
  bed: number | null;
  device_category: string;
  device_name: string;
  serial_number: string;
  ip_address: string | null;
  mac_address: string;
  firmware_version: string;
  is_online: boolean;
  is_active: boolean;
  config: Record<string, unknown>;
  last_heartbeat: string | null;
  created_at: string;
  updated_at: string;
}

// ─── Phase 6: Citizen Portal ───

export interface CitizenHealthProfile {
  id: number;
  patient: number;
  preferred_language: string;
  emergency_contacts: Array<Record<string, unknown>>;
  allergies_summary: string;
  chronic_conditions_summary: string;
  medication_summary: string;
  vaccination_summary: string;
  notification_preferences: Record<string, boolean>;
  consent_settings: Record<string, boolean>;
  portal_enabled: boolean;
  last_portal_login: string | null;
  created_at: string;
  updated_at: string;
}

// ─── Phase 6: Security Enhancement ───

export interface BehavioralAnomaly {
  user_id: number;
  user_email: string;
  period_days: number;
  anomaly_score: number;
  findings: string[];
  unusual_hour_actions: number;
  high_risk_events: number;
  distinct_ips: number;
}

// ─── Phase 6: Event Stream ───

export interface EventStreamLog {
  id: number;
  event_id: string;
  event_source: string;
  event_type: string;
  event_version: string;
  aggregate_type: string;
  aggregate_id: string;
  data: Record<string, unknown>;
  metadata: Record<string, unknown>;
  correlation_id: string;
  causation_id: string;
  occurred_at: string;
  processed_at: string;
}

// ─── Phase 7: AI Orchestrator ───

export type AIRecommendationType =
  | "clinical" | "medication" | "diagnostic" | "follow_up" | "preventive" | "lifestyle";

export type AIRecommendationPriority = "information" | "suggestion" | "recommendation" | "alert";

export interface AIRecommendation {
  id: number;
  recommendation_type: AIRecommendationType;
  priority: AIRecommendationPriority;
  patient: number | null;
  patient_name: string;
  visit: number | null;
  title: string;
  recommendation_text: string;
  clinical_rationale: string;
  supporting_evidence: string[];
  confidence_score: number;
  source_service: string;
  is_accepted: boolean | null;
  accepted_by: number | null;
  accepted_by_name: string;
  accepted_at: string | null;
  rejection_reason: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

// ─── Phase 7: Epidemic Intelligence ───

export type AlertLevel = "green" | "yellow" | "orange" | "red" | "critical";
export type AlertSource = "syndromic" | "lab" | "hospital" | "pharmacy" | "school" | "wearable" | "other";

export interface EpidemicAlert {
  id: number;
  alert_level: AlertLevel;
  alert_level_display: string;
  alert_source: AlertSource;
  alert_source_display: string;
  disease_code: string;
  disease_name: string;
  county: string;
  sub_county: string;
  confirmed_cases: number;
  suspected_cases: number;
  reported_deaths: number;
  attack_rate: number;
  doubling_time_days: number | null;
  r0_estimate: number | null;
  signal_strength: number;
  recommended_actions: string;
  is_active: boolean;
  resolved_at: string | null;
  detected_at: string;
  created_at: string;
}

export interface RegionalSpread {
  disease_code: string;
  period_days: number;
  total_cases: number;
  affected_counties: number;
  county_breakdown: { county: string; cases: number }[];
  spread_pattern: string;
}

export interface PublicHealthForecast {
  id: number;
  forecast_category: string;
  county: string;
  disease_code: string;
  disease_name: string;
  forecast_date: string;
  predicted_cases: number;
  predicted_lower: number | null;
  predicted_upper: number | null;
  trend_direction: string;
  risk_level: string;
  model_name: string;
  created_at: string;
}

// ─── Phase 7: Precision Health ───

export type RiskCategory = "cardiovascular" | "diabetes" | "respiratory" | "cancer" | "mental_health" | "fall" | "readmission" | "general";
export type RiskLevel = "low" | "moderate" | "high" | "critical";

export interface HealthRiskProfile {
  id: number;
  patient: number;
  patient_name: string;
  risk_category: RiskCategory;
  risk_category_display: string;
  risk_score: number;
  risk_level: RiskLevel;
  contributing_factors: string[];
  protective_factors: string[];
  longitudinal_trend: number[];
  last_assessed_at: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PatientRiskSummary {
  patient_id: number;
  overall_risk: string;
  profiles: {
    category: string;
    score: number;
    level: string;
    assessed_at: string;
    factors: string[];
  }[];
}

// ─── Phase 7: Smart Device Events ───

export type DeviceEventCategory = "patient_alert" | "device_status" | "environmental" | "location" | "emergency" | "routine";
export type DeviceEventSeverity = "info" | "warning" | "critical" | "emergency";

export interface SmartDeviceEvent {
  id: number;
  device: number;
  device_name: string;
  hospital: number;
  ward: number | null;
  ward_name: string;
  event_category: DeviceEventCategory;
  event_type: string;
  value: number | null;
  unit: string;
  payload: Record<string, unknown>;
  severity: DeviceEventSeverity;
  is_processed: boolean;
  occurred_at: string;
  created_at: string;
}

export interface DeviceHealth {
  device_id: number;
  device_name: string;
  category: string;
  is_online: boolean;
  is_active: boolean;
  last_heartbeat: string | null;
  events_24h: number;
  errors_24h: number;
  health_score: number;
  status: string;
}

export interface HospitalIoTSummary {
  hospital_id: number;
  total_devices: number;
  online: number;
  offline: number;
  events_last_hour: number;
  critical_events_last_hour: number;
  uptime_pct: number;
}

// ─── Phase 7: Infrastructure Events ───

export type InfraEventType = "scaling" | "health_check" | "alert" | "recovery" | "config" | "deployment" | "performance";

export interface InfrastructureEvent {
  id: number;
  event_type: InfraEventType;
  severity: string;
  service_name: string;
  host_name: string;
  message: string;
  metric_data: Record<string, unknown>;
  auto_action_taken: string;
  auto_action_success: boolean | null;
  resolved: boolean;
  resolved_at: string | null;
  occurred_at: string;
  created_at: string;
}

// ─── Phase 7: Telemedicine Interaction ───

export type InteractionType = "message" | "file" | "prescription" | "note" | "system";

export interface TelemedicineInteraction {
  id: number;
  session: number;
  sender: number;
  sender_name: string;
  interaction_type: InteractionType;
  content: string;
  file_url: string;
  metadata: Record<string, unknown>;
  is_encrypted: boolean;
  created_at: string;
}

// ─── Phase 7: Predictive Metric ───

export interface PredictiveMetric {
  id: number;
  metric_category: string;
  hospital: number | null;
  county: string;
  metric_name: string;
  predicted_value: number;
  actual_value: number | null;
  confidence_interval_lower: number | null;
  confidence_interval_upper: number | null;
  prediction_date: string;
  forecast_horizon_days: number;
  model_name: string;
  features_used: string[];
  created_at: string;
}

// ─── Phase 7: Event Stream ───

export interface EventChainItem {
  event_id: string;
  source: string;
  type: string;
  occurred_at: string;
  duration_from_previous_s: number | null;
}

export interface CorrelatedEvents {
  aggregate_type: string;
  aggregate_id: string;
  total_events: number;
  timeline: {
    event_id: string;
    source: string;
    type: string;
    time: string;
    summary: string;
  }[];
}

// ─── Phase 7: Automation ───

export interface PatientFlowAnalysis {
  hospital_id: number;
  period_days: number;
  avg_daily_admissions: number;
  avg_daily_discharges: number;
  peak_activity_hour: number | null;
  admission_trend: string;
}

export interface Bottleneck {
  ward_id: number;
  ward_name: string;
  type: string;
  severity: string;
  utilization_pct: number;
  recommendation: string;
}

export interface PredictiveStaffing {
  hospital_id: number;
  forecast_days: number;
  avg_daily_admissions: number;
  current_occupancy: number;
  total_beds: number;
  projected_occupancy: number;
  recommended_staff_ratio: string;
}

export interface ScalingRecommendation {
  component: string;
  action: string;
  reason: string;
  priority: string;
}

export interface OperationalAnomaly {
  type: string;
  severity: string;
  value: number;
  message: string;
}

export interface ResourceForecast {
  hospital_id: number;
  forecast_horizon_days: number;
  current_beds: { total: number; occupied: number; available: number };
  avg_daily_admissions: number;
  projected_occupancy_in_days: Record<string, number>;
  capacity_risk: string;
}

// ─── Phase 7: Citizen Super Portal ───

export interface CitizenFullHealthRecord {
  patient: {
    health_id: string;
    full_name: string;
    date_of_birth: string | null;
    gender: string;
    blood_group: string;
    phone: string;
    email: string;
  };
  profile: {
    preferred_language: string;
    allergies: string;
    chronic_conditions: string;
    medications: string;
    emergency_contacts: Record<string, unknown>[];
  };
  recent_visits: { id: number; date: string; complaint: string; doctor: string }[];
  diagnoses: { name: string; icd: string; severity: string; date: string }[];
  active_prescriptions: { medication: string; dosage: string; frequency: string; prescribed_at: string }[];
  lab_results: { test: string; result: string; abnormal: boolean; date: string | null }[];
  wearable_devices: { id: number; type: string; name: string; verified: boolean; last_sync: string | null }[];
  latest_readings: Record<string, { value: number; unit: string; recorded_at: string }>;
  telemedicine: { id: number; doctor: string; scheduled: string; status: string; type: string }[];
  ai_insights: { id: number; type: string; title: string; confidence: string; created: string }[];
  ai_recommendations: { id: number; type: string; title: string; priority: string; created: string }[];
}

export interface EmergencyProfile {
  patient: { full_name: string; health_id: string; blood_group: string; date_of_birth: string | null };
  emergency: { contacts: Record<string, unknown>[]; allergies: string; chronic_conditions: string; medications: string };
  active_prescriptions: { medication_name: string; dosage: string; frequency: string }[];
}

export interface HealthShareResult {
  share_token: string;
  expires_at: string;
}

export interface CareReminder {
  type: string;
  message: string;
  priority: string;
}

// ─── Phase 8: National Intelligent Healthcare Ecosystem ───

// Emergency Response
export type EmergencyType = "natural_disaster" | "pandemic" | "mass_casualty" | "terrorism" | "infrastructure" | "other";
export type EmergencySeverity = "level_1" | "level_2" | "level_3" | "level_4" | "level_5";
export type EmergencyStatus = "active" | "responding" | "contained" | "resolved" | "aftermath";

export interface EmergencyResponseEvent {
  id: number;
  emergency_type: EmergencyType;
  severity: EmergencySeverity;
  status: EmergencyStatus;
  title: string;
  description: string;
  location_region: string;
  affected_counties: string[];
  affected_population: number;
  estimated_casualties: number;
  hospital_capacity_impact: Record<string, unknown>;
  resource_needs: Record<string, unknown>;
  responding_units: Record<string, unknown>[];
  coordination_center: string;
  incident_commander: number | null;
  escalated_at: string | null;
  contained_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

// Predictive Forecast
export type ForecastDomain = "disease" | "mortality" | "demand" | "capacity" | "staffing" | "equipment" | "financial" | "emergency";

export interface PredictiveForecast {
  id: number;
  domain: ForecastDomain;
  hospital: number | null;
  county: string;
  region: string;
  metric_name: string;
  predicted_value: number;
  actual_value: number | null;
  predicted_lower: number | null;
  predicted_upper: number | null;
  forecast_date: string;
  trend_direction: string;
  model_name: string;
  created_at: string;
}

// Infrastructure Twin
export type TwinType = "hospital" | "regional" | "emergency" | "population" | "equipment";

export interface InfrastructureTwin {
  id: number;
  twin_type: TwinType;
  name: string;
  hospital: number | null;
  region: string;
  description: string;
  simulation_status: string;
  current_parameters: Record<string, unknown>;
  simulation_results: Record<string, unknown>;
  baseline_metrics: Record<string, unknown>;
  predictive_scenarios: Record<string, unknown>[];
  last_simulated_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// AI Model Registry
export interface AIModelRegistry {
  id: number;
  model_name: string;
  model_version: string;
  model_type: string;
  description: string;
  status: string;
  performance_metrics: Record<string, unknown>;
  governance_approval: boolean;
  approved_by: number | null;
  approved_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Smart Hospital Metric
export interface SmartHospitalMetric {
  id: number;
  hospital: number;
  ward: number | null;
  metric_category: string;
  metric_name: string;
  metric_value: number;
  unit: string;
  is_alert: boolean;
  recorded_at: string;
  created_at: string;
}

// Population Health Insight
export interface PopulationHealthInsight {
  id: number;
  category: string;
  county: string;
  sub_county: string;
  indicator_name: string;
  indicator_value: number;
  population_base: number;
  trend_direction: string;
  comparison_national: number | null;
  comparison_regional: number | null;
  period_start: string;
  period_end: string;
  created_at: string;
}

// Operational Alert
export interface OperationalAlert {
  id: number;
  category: string;
  severity: string;
  hospital: number | null;
  title: string;
  description: string;
  metric_name: string;
  metric_value: number | null;
  source_service: string;
  recommended_action: string;
  is_acknowledged: boolean;
  is_resolved: boolean;
  created_at: string;
}

// Device Telemetry
export interface DeviceTelemetryEvent {
  id: number;
  device: number;
  hospital: number;
  telemetry_type: string;
  metric_name: string;
  metric_value: number;
  unit: string;
  signal_strength: number | null;
  battery_level: number | null;
  is_abnormal: boolean;
  recorded_at: string;
  ingested_at: string;
}

// Operations Intelligence
export interface HospitalLoadAnalysis {
  hospital_id: number;
  period_days: number;
  bed_occupancy_pct: number;
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  avg_daily_admissions: number;
  avg_daily_discharges: number;
  staff_utilization_pct: number;
  efficiency_score: number;
}

export interface ResourceAllocation {
  hospital_id: number;
  forecast_days: number;
  projected_bed_need: number;
  projected_staff_need: number;
  projected_equipment_need: Record<string, number>;
  current_capacity: Record<string, number>;
  risk_level: string;
}

export interface NationalEmergencyOverview {
  total_active: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  affected_regions: string[];
  total_affected_population: number;
  hospitals_impacted: number;
}

export interface RegionalCapacity {
  region: string;
  total_hospitals: number;
  total_beds: number;
  available_beds: number;
  icu_beds: number;
  available_icu: number;
  emergency_rooms_available: number;
  staffing_level: string;
}

export interface ModelGovernanceReport {
  model_id: number;
  model_name: string;
  model_version: string;
  model_type: string;
  status: string;
  governance_approval: boolean;
  total_inferences: number;
  avg_confidence: number;
  last_used: string | null;
  audit_entries: number;
}

export interface EfficiencyScore {
  hospital_id: number;
  overall_score: number;
  bed_utilization_score: number;
  staff_efficiency_score: number;
  operational_score: number;
  patient_flow_score: number;
  recommendations: string[];
}

export interface ThreatIntelReport {
  period_days: number;
  total_threats_detected: number;
  critical_threats: number;
  by_category: Record<string, number>;
  top_affected_users: { user_id: number; email: string; count: number }[];
  anomalies_detected: number;
  recommendations: string[];
}

export interface PopulationTrend {
  indicator: string;
  county: string;
  data_points: { period: string; value: number }[];
  trend_direction: string;
  change_pct: number;
}

export interface TwinSimulationResult {
  twin_id: number;
  twin_name: string;
  simulation_status: string;
  results: Record<string, unknown>;
  scenarios: number;
  last_simulated: string | null;
}

export interface DeviceTelemetryAnalytics {
  device_id: number;
  total_readings: number;
  abnormal_readings: number;
  avg_signal_strength: number | null;
  avg_battery_level: number | null;
  by_type: Record<string, number>;
  last_reading: string | null;
}

export interface HospitalTelemetryDashboard {
  hospital_id: number;
  total_devices_reporting: number;
  total_telemetry_events_24h: number;
  abnormal_events: number;
  by_type: Record<string, number>;
  top_alerting_devices: { device_id: number; device_name: string; alert_count: number }[];
}
