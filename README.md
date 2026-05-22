# MediRecord EHR - Hospital Electronic Health Record System

Secure, scalable hospital infrastructure software built with Next.js, Django REST Framework, and PostgreSQL.

## Architecture

```
hospital-ehr/
├── backend/                    # Django REST API
│   ├── config/                 # Django settings, URLs, WSGI
│   ├── core/                   # Models, permissions, pagination, exceptions
│   ├── api/
│   │   ├── authentication/     # JWT auth, login, logout, user management
│   │   ├── patients/           # Patient CRUD, search, medical history
│   │   ├── clinical/           # Visits, vitals, diagnoses, prescriptions
│   │   ├── labs/               # Lab requests and results
│   │   ├── timeline/           # Unified patient medical timeline
│   │   ├── admissions/         # Wards, beds, admissions, discharge, transfer
│   │   ├── billing/            # Invoices, payments
│   │   ├── imaging/            # Imaging requests and results
│   │   ├── notifications/      # User notifications
│   │   ├── reports/            # Dashboard stats, revenue, clinical reports
│   │   └── audit/              # Audit log viewer
│   ├── middleware/              # Audit logging, rate limiting
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js 14 application
│   ├── src/
│   │   ├── app/                # Pages (login, dashboard, patients, admissions, billing, imaging, operations)
│   │   ├── components/
│   │   │   ├── layout/         # Sidebar, navbar
│   │   │   ├── ui/             # Loading spinner, pagination
│   │   │   └── clinical/       # Visit, vitals, diagnosis, Rx, labs, timeline tabs
│   │   └── lib/
│   │       ├── api/            # API clients (patients, clinical, labs, timeline, admissions, billing, imaging, notifications, reports)
│   │       ├── api.ts          # Axios instance with JWT interceptors
│   │       ├── auth.ts         # Auth service (login, logout, token management)
│   │       ├── auth-context.tsx # React auth context
│   │       └── types.ts        # All TypeScript interfaces
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Features (Phase 1, 2 & 3)

### Authentication & Authorization
- JWT-based authentication with access/refresh tokens
- 8 role levels with strict RBAC (Super Admin → Patient)
- Backend-only authorization enforcement
- Rate limiting on login and API endpoints
- Session expiration and token refresh

### Patient Management
- Patient registration with unique Health ID generation
- QR code for patient identification
- Full patient profiles (demographics, contacts, medical info)
- Instant search across name, ID, phone, national ID
- Pagination, filtering by gender and blood group

### Clinical Workflow (Phase 2)
- **Visit/Encounter system** - Start, update, close patient visits
- **Vital Signs** - Record temperature, BP, pulse, SpO2, weight, height, BMI
- **Diagnosis** - Primary/secondary diagnosis with ICD codes and severity
- **Prescriptions** - Medication prescribing with frequency, route, duration
- **Lab Requests & Results** - Order lab tests, upload results with attachments
- **Patient Medical Timeline** - Unified chronological view of all clinical events
- **Doctor Dashboard** - Active visits, pending labs, quick patient access

### Security
- All permissions enforced server-side
- Audit logging for every data access and modification
- CSRF protection, SQL injection prevention (ORM)
- Input validation and sanitization
- HTTPS-ready configuration
- Password hashing (Django default, PBKDF2)
- Token blacklisting on logout
- Environment-based configuration

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- Docker (optional, for containerized setup)

### 1. Database Setup

```bash
# Create PostgreSQL database
psql -U postgres
CREATE DATABASE ehr_hospital;
CREATE USER ehr_admin WITH PASSWORD 'ehr_admin_password';
GRANT ALL PRIVILEGES ON DATABASE ehr_hospital TO ehr_admin;
\q
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py makemigrations core
python manage.py migrate

# Create super admin user
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Run development server
npm run dev
```

### 4. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin/
- **API Docs (Swagger):** http://localhost:8000/api/docs/

### Docker Setup (Alternative)

```bash
# Start all services
docker-compose up -d

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | Login, returns JWT tokens |
| POST | `/api/auth/logout/` | Logout, blacklists refresh token |
| GET | `/api/auth/me/` | Get current user |
| POST | `/api/auth/refresh/` | Refresh access token |
| POST | `/api/auth/change-password/` | Change password |
| POST | `/api/auth/users/` | Create user (admin only) |
| GET | `/api/auth/users/` | List users |

### Patients
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/patients/` | List/search patients with pagination |
| POST | `/api/patients/` | Register new patient |
| GET | `/api/patients/{id}/` | Get patient details |
| PATCH | `/api/patients/{id}/` | Update patient |
| DELETE | `/api/patients/{id}/` | Deactivate patient |
| GET | `/api/patients/quick_search/?q=` | Instant search (top 10) |
| GET | `/api/patients/{id}/history/` | Get medical history |
| POST | `/api/patients/{id}/add_history/` | Add medical record |

### Clinical - Visits
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/clinical/visits/` | List visits (filterable by patient, status) |
| POST | `/api/clinical/visits/` | Start new visit |
| GET | `/api/clinical/visits/{id}/` | Get visit detail with diagnoses, Rx, vitals |
| PATCH | `/api/clinical/visits/{id}/` | Update visit |
| POST | `/api/clinical/visits/{id}/close/` | Close visit |
| GET | `/api/clinical/visits/{id}/timeline/` | Get visit timeline |

### Clinical - Vital Signs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/clinical/vitals/` | List vitals (filterable by patient, visit) |
| POST | `/api/clinical/vitals/` | Record vitals (nurses) |

### Clinical - Diagnoses
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/clinical/diagnoses/` | List diagnoses (searchable) |
| POST | `/api/clinical/diagnoses/` | Record diagnosis (doctors) |
| PATCH | `/api/clinical/diagnoses/{id}/` | Update diagnosis |

### Clinical - Prescriptions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/clinical/prescriptions/` | List prescriptions |
| POST | `/api/clinical/prescriptions/` | Create prescription (doctors) |
| POST | `/api/clinical/prescriptions/dispense/` | Mark prescriptions as dispensed (pharmacists) |

### Labs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/labs/requests/` | List lab requests (filterable by status, priority) |
| POST | `/api/labs/requests/` | Request lab test (doctors) |
| PATCH | `/api/labs/requests/{id}/` | Update request status |
| POST | `/api/labs/requests/{id}/cancel/` | Cancel lab request |
| GET | `/api/labs/results/` | List lab results |
| POST | `/api/labs/results/` | Upload lab result with attachment |

### Timeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/timeline/patient/{patient_id}/` | Get unified patient medical timeline |

### Admissions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admissions/wards/` | List wards |
| GET | `/api/admissions/wards/{id}/beds/` | List beds in a ward |
| GET | `/api/admissions/beds/` | List all beds (filterable) |
| GET | `/api/admissions/admissions/` | List admissions (filterable) |
| POST | `/api/admissions/admissions/` | Admit patient |
| POST | `/api/admissions/admissions/{id}/discharge/` | Discharge patient |
| POST | `/api/admissions/admissions/{id}/transfer/` | Transfer patient |

### Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/billing/invoices/` | List invoices (filterable) |
| POST | `/api/billing/invoices/` | Create invoice |
| GET | `/api/billing/invoices/{id}/` | Get invoice detail |
| GET | `/api/billing/payments/` | List payments |
| POST | `/api/billing/payments/` | Record payment |

### Imaging
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/imaging/requests/` | List imaging requests |
| POST | `/api/imaging/requests/` | Create imaging request |
| GET | `/api/imaging/results/` | List imaging results |
| POST | `/api/imaging/results/` | Upload imaging result |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications/` | List user notifications |
| GET | `/api/notifications/unread_count/` | Unread notification count |
| POST | `/api/notifications/{id}/mark_read/` | Mark notification read |
| POST | `/api/notifications/mark_all_read/` | Mark all read |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/dashboard/` | Hospital dashboard stats |
| GET | `/api/reports/revenue/` | Revenue report (query: ?days=30) |
| GET | `/api/reports/clinical/` | Clinical activity report |

### Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit/logs/` | List audit logs (super admin only) |

## Role-Based Access Control

| Module | Super Admin | Hospital Admin | Doctor | Nurse | Lab Tech | Pharmacist | Receptionist | Patient |
|--------|:-----------:|:--------------:|:------:|:-----:|:--------:|:----------:|:------------:|:-------:|
| View Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Register Patient | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Search Patients | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| View Patient Profile | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Own only |
| Edit Patient | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Start Visit | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Record Vitals | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Record Diagnosis | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Prescribe Medication | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Dispense Medication | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Request Lab Test | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Upload Lab Result | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| View Timeline | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Own only |
| View Audit Logs | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage Users | ✅ | Limited | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | (required) |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `DB_NAME` | PostgreSQL database name | `ehr_hospital` |
| `DB_USER` | Database user | `ehr_admin` |
| `DB_PASSWORD` | Database password | (required) |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access token expiry | `30` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Refresh token expiry | `1` |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend origins | `http://localhost:3000` |
| `HTTPS_ONLY` | Enforce HTTPS | `True` |
| `AUDIT_LOG_ENABLED` | Enable audit logging | `True` |

### Frontend (`frontend/.env.local`)
| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## Database Models (Phase 1, 2 & 3)

### Visit
| Field | Type | Notes |
|-------|------|-------|
| patient | FK → Patient | |
| doctor | FK → User | Doctor conducting the visit |
| visit_date | DateTime | Indexed |
| chief_complaint | Text | Patient's main reason |
| symptoms | Text | Structured symptom list |
| diagnosis_summary | Text | |
| treatment_plan | Text | |
| follow_up_date | Date | |
| status | Choice | in_progress, completed, cancelled, follow_up |

### VitalSign
| Field | Type | Notes |
|-------|------|-------|
| visit | FK → Visit | |
| patient | FK → Patient | |
| temperature | Decimal | Celsius |
| blood_pressure_systolic | Integer | mmHg |
| blood_pressure_diastolic | Integer | mmHg |
| pulse_rate | Integer | bpm |
| respiratory_rate | Integer | breaths/min |
| oxygen_saturation | Decimal | % |
| weight | Decimal | kg |
| height | Decimal | cm |
| bmi | Decimal | Auto-calculated |

### Diagnosis
| Field | Type | Notes |
|-------|------|-------|
| visit | FK → Visit | |
| patient | FK → Patient | |
| diagnosis_type | Choice | primary, secondary |
| diagnosis_name | CharField(500) | |
| icd_code | CharField(20) | Indexed |
| severity | Choice | mild, moderate, severe, critical |
| is_confirmed | Boolean | |

### Prescription
| Field | Type | Notes |
|-------|------|-------|
| visit | FK → Visit | |
| patient | FK → Patient | |
| medication_name | CharField(300) | Indexed |
| dosage | CharField(100) | e.g. 500mg |
| frequency | Choice | od, bd, tds, qid, qhs, prn, stat |
| route | Choice | oral, iv, im, sc, topical, etc. |
| duration_days | Integer | |
| is_dispensed | Boolean | |
| dispensed_by | FK → User | Pharmacist |

### LabRequest
| Field | Type | Notes |
|-------|------|-------|
| visit | FK → Visit | |
| patient | FK → Patient | |
| test_name | CharField(300) | Indexed |
| priority | Choice | routine, urgent, stat |
| status | Choice | requested, sample_collected, in_progress, completed, cancelled |

### LabResult
| Field | Type | Notes |
|-------|------|-------|
| lab_request | OneToOne → LabRequest | |
| patient | FK → Patient | |
| result_data | JSONField | Flexible structured results |
| result_text | TextField | |
| is_abnormal | Boolean | |
| file_attachment | FileField | PDF, images |

### Ward
| Field | Type | Notes |
|-------|------|-------|
| ward_name | CharField(100) | |
| ward_type | Choice | general, private, icu, pediatrics, maternity, surgery, isolation |
| capacity | Integer | Total bed count |
| description | TextField | |
| is_active | Boolean | |

### Bed
| Field | Type | Notes |
|-------|------|-------|
| ward | FK → Ward | |
| bed_number | CharField(20) | |
| occupancy_status | Choice | available, occupied, maintenance |

### Admission
| Field | Type | Notes |
|-------|------|-------|
| patient | FK → Patient | |
| ward | FK → Ward | |
| bed | FK → Bed | |
| admission_reason | TextField | |
| status | Choice | active, discharged, transferred |
| discharge_notes | TextField | |

### Invoice
| Field | Type | Notes |
|-------|------|-------|
| invoice_number | CharField(20) | Auto-generated |
| patient | FK → Patient | |
| visit | FK → Visit (nullable) | |
| admission | FK → Admission (nullable) | |
| consultation_fee | Decimal | Default 0 |
| lab_fee, pharmacy_fee | Decimal | |
| admission_fee, radiology_fee | Decimal | |
| other_fees, discount, tax | Decimal | |
| total_amount | Decimal | Auto-calculated |
| amount_paid, balance | Decimal | Auto-calculated |
| status | Choice | pending, paid, partially_paid, cancelled |

### Payment
| Field | Type | Notes |
|-------|------|-------|
| invoice | FK → Invoice | |
| amount_paid | Decimal | |
| payment_method | Choice | cash, card, mpesa, insurance, bank_transfer |
| transaction_reference | CharField(100) | |

### ImagingRequest
| Field | Type | Notes |
|-------|------|-------|
| visit | FK → Visit | |
| patient | FK → Patient | |
| imaging_type | Choice | xray, mri, ct_scan, ultrasound, mammography, pet_scan |
| priority | Choice | routine, urgent, stat |
| status | Choice | requested, scheduled, completed, cancelled |
| region_examined | CharField(200) | |
| clinical_history | TextField | |

### ImagingResult
| Field | Type | Notes |
|-------|------|-------|
| imaging_request | OneToOne → ImagingRequest | |
| patient | FK → Patient | |
| findings | TextField | |
| impression | TextField | |
| report | TextField | |
| radiologist | FK → User | |
| is_abnormal | Boolean | |
| image_file | FileField | |
| report_file | FileField | |

### Notification
| Field | Type | Notes |
|-------|------|-------|
| recipient | FK → User | |
| patient | FK → Patient (nullable) | |
| category | Choice | lab_result, imaging, admission, billing, appointment, general |
| title | CharField(200) | |
| message | TextField | |
| is_read | Boolean | |
| link | CharField(500) | Deep link to relevant page |

## Design Principles

- **Security-first:** All authorization is enforced server-side. Frontend roles are display-only.
- **Minimal latency:** Database queries use indexed fields. All clinical data loads in parallel.
- **Clean architecture:** Modular apps with separation of concerns. Each clinical domain is independent.
- **Production-ready:** Environment-based config, Docker support, gunicorn, static file serving.
- **Audit trail:** Every create/update/delete operation is logged with user, IP, and timestamp.
- **Doctor-first UX:** The patient profile integrates all clinical workflows into a single tabbed interface. Minimal clicks from search → profile → clinical action.

## Phase 4: National Health Infrastructure (Complete)

### Multi-Hospital Architecture
- Hospital model with 7 types (national_referral → clinic), county and type indexing
- HospitalStaff membership with 9 specialized staff roles
- Department model per hospital
- Automatic hospital-level data isolation for all non-super-admin users

### National Patient Identity
- `PatientIdentity` model with national health ID generation (`NHID-XXXX-XXXX-XXXX`)
- Duplicate detection using weighted similarity scoring (name, DOB, national ID, phone)
- Patient merge with full history reassignment and audit trail
- `PatientMergeLog` for forensic merge tracking

### Cross-Hospital Referrals
- Full referral lifecycle: pending → accept/decline → complete
- Priority-based routing (routine/urgent/emergency)
- Automatic notifications to receiving hospital staff
- Document attachment support
- Audit logging on every referral action

### Offline-First Sync Engine
- `SyncQueue` with create/update/delete actions per resource type
- Automatic retry with configurable max retries (default 3)
- Conflict detection and manual resolution support
- Celery beat processes queues every 60 seconds
- Sync logging with duration tracking

### Enterprise Analytics
- Hospital dashboard metrics (patients, visits, revenue, diagnoses)
- Disease trend analysis with monthly aggregation
- Revenue analysis with monthly breakdown
- Department utilization tracking
- National aggregate statistics (super admin only)

### Telemedicine Foundation
- Session model with video/audio/chat types
- Full lifecycle: scheduled → in_progress → completed/cancelled/missed
- Meeting URL support for future video integration
- Hospital-scoped session management

### Insurance/SHA Readiness
- Multi-provider support (SHA, NHIF, Private, Community)
- Coverage verification service layer
- Claims submission with full audit trail
- Structured for future live API integration

### Enterprise Security
- Hospital isolation middleware enforces tenant boundaries
- Enhanced RBAC with hospital-scoped permissions
- Per-user and per-hospital rate limiting via Redis
- EnterpriseAuditEvent with severity levels and event types
- Super admin bypasses all isolation constraints

### Async Infrastructure
- Celery worker with Redis broker/backend
- Beat schedule: sync queue processing (60s), analytics snapshots (1h), cleanup tasks (daily)
- Task modules: sync, analytics, maintenance

### Deployment
- Multi-service Docker Compose (postgres, redis, backend, celery_worker, celery_beat, frontend, nginx)
- Nginx reverse proxy with security headers
- Sentry error tracking support
- Cloud object storage (S3) support
- Whitenoise for static file serving

## Security Notes

- Passwords are hashed using Django's default PBKDF2 algorithm
- JWT tokens are blacklisted on logout
- Rate limiting prevents brute-force attacks
- SQL injection is prevented through Django ORM parameterized queries
- CSRF protection is enabled
- Security headers are set (HSTS, XSS, content-type)
- CORS is restricted to allowed origins
- All clinical permissions enforced server-side per role
- Patient access restricted to own records only
- Hospital-level data isolation with tenant-aware middleware
- Enterprise audit events with severity classification
- Per-user and per-hospital rate limiting via Redis

## Future Phases

- **Phase 5:** Pharmacy inventory management, procurement, appointments scheduling
- **Phase 6:** AI diagnosis assistance, risk prediction, anomaly detection
- **Phase 7:** Wearable integration, biometric authentication, smart hospital IoT
