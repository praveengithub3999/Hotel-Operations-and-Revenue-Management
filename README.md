# 🏨 Hotel Operations & Revenue Management System

An enterprise-grade, asynchronous RESTful API for modern hotel operations, reservation management, housekeeping, maintenance workflows, guest experience tracking, and real-time revenue analytics. Built with **FastAPI**, **PostgreSQL** (SQLAlchemy 2.0), **MongoDB**, and **Docker**.

---

## 📑 Table of Contents
1. [Architectural Overview](#-architectural-overview)
2. [Team Division of Responsibilities](#-team-division-of-responsibilities)
3. [Advanced Features (Section 28 Compliance)](#-advanced-features-section-28-compliance)
4. [Database Design](#-database-design)
5. [Complete API Reference](#-complete-api-reference)
6. [Getting Started & Local Setup](#-getting-started--local-setup)
7. [Running with Docker](#-running-with-docker)
8. [Testing & Quality Assurance](#-testing--quality-assurance)

---

## 🏛 Architectural Overview

The application strictly implements **Section 30 Object-Oriented Architecture** using a layered **Domain-Driven Design (DDD)** pattern:

```
[ HTTP Client / Frontend ]
          │
          ▼
┌──────────────────────────────────────────────┐
│             FastAPI Routers                  │ (app/api/)
│  - Request validation & serialization        │
│  - JWT Authentication & RBAC enforcement     │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              Service Layer                   │ (app/services/)
│  - Business logic, algorithms, transactions  │
│  - Dynamic pricing, cancellation policies    │
│  - Housekeeping workflows, SLA tracking      │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│            Repository Layer                  │ (app/repositories/)
│  - Abstracted query interface (BaseRepository)│
│  - Pure database persistence logic           │
└──────────────┬───────────────────────┬───────┘
               │                       │
               ▼                       ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│ PostgreSQL (Relational)   │ │   MongoDB (Document Store)│
│ - Strict ACID folios      │ │ - Unstructured logs       │
│ - Financial ledger        │ │ - Audit trails            │
│ - Reservations & inventory│ │ - Guest feedback          │
└───────────────────────────┘ └───────────────────────────┘
```

### Key Architectural Standards
- **Layer Decoupling**: API routers do not execute direct SQL or access ORM sessions; they delegate exclusively to services. Services communicate with the database via repositories.
- **Strict Decimal Precision**: All monetary operations use Python `Decimal` to avoid floating-point inaccuracies.
- **Dual Database Strategy**:
  - **PostgreSQL**: Handles operational data, relational constraints, foreign keys, and financial integrity.
  - **MongoDB**: Handles time-series audit logs, housekeeping transition history, maintenance logs, and rich guest feedback.

---

## 👥 Team Division of Responsibilities

### 🔹 Member 1: Core Operations (Rooms & Reservations)
- **Room Inventory & Catalog**: Manage hotels, room types, and individual room configurations (`POST /hotels`, `POST /room-types`, `POST /rooms`, `PUT /rooms/{id}`).
- **Dynamic Pricing Engine**: Algorithmic night rate calculation based on base price, weekend surcharges, peak seasonal months, and current hotel occupancy.
- **Date-Range Availability Engine**: `GET /rooms/availability` filtering rooms by date overlap, type, and operational status.
- **Reservation Lifecycle**: Booking creation, date modification (`PUT /reservations/{id}`), check-in/check-out date validation, double-booking prevention.
- **Cancellation Policy Tier Engine**: Multi-tiered refund calculation based on cancellation notice window.
- **No-Show Automation**: Scheduled batch processing endpoint (`POST /reservations/no-shows/process`) transitioning overdue bookings to `NO_SHOW`.

### 🔹 Member 2: Guest Experience & Housekeeping Operations
- **Guest Profiles**: Complete guest registry (`POST /guests`, `GET /guests/{id}`, `GET /guests/history/{id}`) with contact details and emergency contacts.
- **Front Desk Orchestration**: Check-in validation (`POST /reservations/{id}/check-in`) ensuring room cleanliness, and check-out processing (`POST /reservations/{id}/check-out`) verifying balance clearance.
- **Housekeeping State Machine**: Comprehensive room cleanliness progression (`DIRTY` ➔ `CLEANING` ➔ `CLEAN` ➔ `INSPECTED`) via `app/services/housekeeping_service.py` and direct room status update (`PUT /rooms/{id}/housekeeping-status`).
- **Staff Task Assignments**: Housekeeping and maintenance assignments (`POST /staff/assignments`, `GET /staff/assignments`) with shift tracking.
- **Maintenance & SLA Tracking**: Issue logging, category assignment, urgency tiers, resolution verification, and SLA deadline tracking.
- **Guest Feedback Collection**: MongoDB-backed guest feedback submission and sentiment retrieval (`POST /feedback`, `GET /feedback`).

### 🔹 Member 3: Billing, Payments & Revenue Management
- **Add-on Services & Folio Billing**: Dynamic charge posting (`POST /charges`) with duplicate charge protection (`charge_fingerprint`), and itemized billing summaries.
- **Discount & Voucher Engine**: Promo code validation, percentage or fixed discounts, minimum spend conditions, and expiry enforcement (`POST /discounts`).
- **Invoicing & Checkout Settlement**: Automated invoice generation (`POST /invoices`), tax calculation, balance reconciliation, and PDF/summary export.
- **Multi-Method Payments & Refunds**: Secure payment processing (`POST /payments`, `GET /payments/{id}`) supporting `CASH`, `CREDIT_CARD`, `DEBIT_CARD`, `UPI`, and `BANK_TRANSFER`, with partial or full refunds (`POST /refunds`).
- **Revenue Analytics & KPI Metrics**:
  - `GET /reports/occupancy`: Occupancy percentage across hotels and date ranges.
  - `GET /reports/revenue`: Financial summaries, total charges, collected payments, outstanding balances, ADR (Average Daily Rate), and RevPAR (Revenue Per Available Room).
  - `GET /reports/room-performance`: Per-room utilization, nights occupied, and total revenue earned.
  - `GET /reports/revenue/breakdown`: Time-series daily and monthly revenue breakdowns.

---

## 🚀 Advanced Features (Section 28 Compliance)

| Feature | Implementation Details | Associated Endpoints |
|---|---|---|
| **1. Dynamic Pricing Engine** | Calculates base price adjusted for weekend nights (+20%), peak holiday months (+30%), and high occupancy (>80% occupancy triggers +15%). | `GET /rooms/{id}/pricing` |
| **2. Cancellation Policy Tiers** | `> 7 days notice`: 100% refund eligible.<br>`2 to 7 days notice`: 50% refund eligible.<br`< 2 days notice`: 0% refund (forfeited). | `DELETE /reservations/{id}` |
| **3. Automated No-Show Processing** | Automatically detects confirmed reservations past 6:00 PM on arrival date and flags them as `NO_SHOW`, freeing room inventory. | `POST /reservations/no-shows/process` |
| **4. Maintenance SLA Monitoring** | Enforces resolution deadlines based on urgency (`HIGH`: 4 hours, `MEDIUM`: 12 hours, `LOW`: 24 hours). Computes SLA breach status. | `GET /maintenance/{id}`, `GET /maintenance/` |
| **5. Duplicate Charge Prevention** | Idempotency safeguard using sha256 charge fingerprints within a 60-second window to prevent accidental double-billing of amenities. | `POST /charges/` |
| **6. Granular Revenue Breakdown** | Daily and monthly aggregations calculating RevPAR, ADR, and occupancy metrics across custom reporting periods. | `GET /reports/revenue/breakdown`, `GET /reports/room-performance` |

---

## 🗄 Database Design

### Relational Schema (PostgreSQL)
- **`hotels`**: ID, name, code, address, phone, email, active status.
- **`room_types`**: ID, hotel_id, name, base_price, capacity, description.
- **`rooms`**: ID, room_type_id, room_number, floor, status (`AVAILABLE`, `OCCUPIED`, `MAINTENANCE`), housekeeping_status (`CLEAN`, `DIRTY`, `CLEANING`, `INSPECTED`).
- **`guests`**: ID, full_name, email, phone, id_proof_number, id_proof_type, emergency_contact.
- **`reservations`**: ID, reservation_number, guest_id, room_id, check_in_date, check_out_date, number_of_guests, status (`CONFIRMED`, `CHECKED_IN`, `CHECKED_OUT`, `CANCELLED`, `NO_SHOW`).
- **`housekeeping_records`**: ID, room_id, assigned_to, task_type, status, priority, started_at, completed_at, remarks.
- **`maintenance_records`**: ID, room_id, issue_description, reported_by, category, priority, status, sla_deadline, resolved_at.
- **`staff_assignments`**: ID, staff_id, staff_name, task_type, target_id, shift, status, assigned_at.
- **`service_requests`**: ID, reservation_id, service_name, quantity, unit_price, total_price, status.
- **`charges`**: ID, reservation_id, charge_type, description, amount, posted_at, charge_fingerprint.
- **`discounts`**: ID, code, description, discount_type (`PERCENTAGE`, `FIXED`), value, min_total_amount, max_discount_amount, is_active.
- **`invoices`**: ID, invoice_number, reservation_id, discount_id, subtotal, discount_amount, tax_amount, total_amount, paid_amount, balance_amount, status (`PENDING`, `PARTIALLY_PAID`, `PAID`).
- **`payments`**: ID, invoice_id, payment_method, amount, transaction_id, status.
- **`refunds`**: ID, payment_id, amount, reason, processed_at.
- **`users`**: ID, username, email, hashed_password, role (`ADMIN`, `MANAGER`, `RECEPTIONIST`, `HOUSEKEEPING`, `MAINTENANCE`), is_active.

### Document Schema (MongoDB Collections)
- **`audit_logs`**: System-wide administrative action logs with actor, event type, metadata, and timestamps.
- **`housekeeping_logs`**: Historical room hygiene changes, inspections, and maid actions.
- **`maintenance_logs`**: Detailed engineering updates, parts replacement, and repair progress logs.
- **`guest_feedback`**: Guest ratings (1-5 stars), category ratings (cleanliness, staff, amenities), comments, and sentiments.

---

## 📡 Complete API Reference

### 🔐 Authentication (`/auth`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/auth/login` | Public | Authenticate user and obtain JWT bearer token |
| `POST` | `/auth/register` | Admin | Register new staff or administrative user |
| `GET` | `/auth/me` | Authenticated | Retrieve current user profile and role |

### 🏨 Hotel & Room Management (`/hotels`, `/room-types`, `/rooms`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/hotels/` | Admin | Create hotel property |
| `GET` | `/hotels/` | Staff | List all hotel properties |
| `GET` | `/hotels/{id}` | Staff | Get hotel details |
| `POST` | `/room-types/` | Admin | Create room type category |
| `GET` | `/room-types/` | Staff | List room types |
| `POST` | `/rooms/` | Admin | Create room inventory record |
| `GET` | `/rooms/` | Staff | List rooms with optional filters |
| `GET` | `/rooms/{id}` | Staff | Get specific room record |
| `PUT` | `/rooms/{id}` | Manager/Admin | Update room attributes (floor, status, pricing) |
| `PUT` | `/rooms/{id}/housekeeping-status` | Housekeeping/Staff | Direct update of room hygiene status |
| `GET` | `/rooms/availability` | Staff | Query available rooms by date window & criteria |
| `GET` | `/rooms/{id}/pricing` | Staff | Calculate real-time dynamic pricing for a date |

### 📅 Reservations & Front Desk (`/reservations`, `/guests`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/guests/` | Receptionist | Register guest profile |
| `GET` | `/guests/` | Receptionist | List guest registry |
| `GET` | `/guests/{id}` | Receptionist | Get guest details |
| `GET` | `/guests/history/{id}` | Receptionist | View guest stay history and lifetime value |
| `POST` | `/reservations/` | Receptionist | Create room reservation |
| `GET` | `/reservations/` | Receptionist | List all reservations |
| `GET` | `/reservations/{id}` | Receptionist | Retrieve reservation folio and stay details |
| `PUT` | `/reservations/{id}` | Receptionist | Modify reservation stay dates or special requests |
| `DELETE`| `/reservations/{id}` | Receptionist | Cancel reservation with automated refund tier calculation |
| `POST` | `/reservations/{id}/check-in` | Receptionist | Process check-in (validates room is clean & available) |
| `POST` | `/reservations/{id}/check-out`| Receptionist | Process check-out (validates zero balance, flags room dirty) |
| `POST` | `/reservations/no-shows/process`| Receptionist | Automatically process overdue confirmed reservations |

### 🧹 Operations & Maintenance (`/housekeeping`, `/maintenance`, `/staff/assignments`, `/feedback`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/housekeeping/` | Housekeeping/Staff | Create housekeeping task |
| `GET` | `/housekeeping/` | Housekeeping/Staff | List tasks with filters (room, status, assigned_to) |
| `PUT` | `/housekeeping/{id}` | Housekeeping/Staff | Update task status (`IN_PROGRESS`, `COMPLETED`) |
| `POST` | `/maintenance/` | Staff | File maintenance issue |
| `GET` | `/maintenance/` | Staff | List maintenance tickets with SLA tracking |
| `GET` | `/maintenance/{id}` | Staff | View ticket details and SLA countdown |
| `PUT` | `/maintenance/{id}` | Maintenance/Staff | Resolve maintenance issue and restore room status |
| `POST` | `/staff/assignments/` | Manager | Assign staff to room cleaning or maintenance |
| `GET` | `/staff/assignments/` | Staff | View active staff assignments |
| `POST` | `/feedback/` | Public/Guest | Submit guest review & rating to MongoDB |
| `GET` | `/feedback/` | Manager | View guest ratings and satisfaction logs |

### 💳 Billing, Invoices & Revenue (`/charges`, `/discounts`, `/invoices`, `/payments`, `/refunds`, `/reports`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/charges/` | Staff | Post amenity or dining charge to guest folio |
| `GET` | `/charges/reservation/{id}` | Staff | Get itemized charges for reservation |
| `POST` | `/discounts/` | Manager | Create discount coupon code |
| `GET` | `/discounts/` | Staff | List active discounts |
| `POST` | `/invoices/` | Receptionist | Generate invoice folio for reservation |
| `GET` | `/invoices/{id}` | Receptionist | View invoice details with balance |
| `POST` | `/payments/` | Receptionist | Process guest payment |
| `GET` | `/payments/{id}` | Receptionist | Retrieve payment receipt |
| `POST` | `/refunds/` | Manager | Process refund for payment |
| `GET` | `/reports/occupancy` | Manager/Admin | Occupancy rate report |
| `GET` | `/reports/revenue` | Manager/Admin | Revenue summary, ADR, RevPAR |
| `GET` | `/reports/room-performance` | Manager/Admin | Per-room revenue and night occupancy |
| `GET` | `/reports/revenue/breakdown` | Manager/Admin | Daily and monthly financial breakdowns |

---

## 🛠 Getting Started & Local Setup

### 1. Prerequisites
- Python 3.12+ (or Python 3.11+)
- PostgreSQL 15+
- MongoDB 6+

### 2. Clone and Setup Environment
```bash
git clone <repo-url>
cd hotel-management-system

# Create and activate virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```ini
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/hotel_management
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=hotel_operations
JWT_SECRET=your_super_secret_jwt_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 4. Database Schema Migration
Run the automated schema synchronization script:
```bash
python scripts/migrate_v2_schema.py
```

### 5. Run Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🐳 Running with Docker

You can spin up the full application stack (FastAPI + PostgreSQL + MongoDB) with a single command:

```bash
docker compose up --build -d
```

To view application logs:
```bash
docker compose logs -f web
```

To stop all containers:
```bash
docker compose down
```

---

## 🧪 Testing & Quality Assurance

The system includes a test suite covering unit, integration, and end-to-end API flows:

### Run All Tests
```bash
pytest -v
```

### Run Tests with Code Coverage
```bash
pytest --cov=app tests/
```

### Test Suite Summary
- **Total Tests**: `123 passed`
- **Total Code Coverage**: `89%`
- **Core Models**: `100%`
- **Repositories**: `80% - 100%`
- **Services**: `74% - 100%`
- **API Routers**: `82% - 100%`
