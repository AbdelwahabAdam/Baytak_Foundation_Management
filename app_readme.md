# Baytak Foundation Management — Application Reference

This document describes the **admin dashboard UI**, **database tables/fields**, and **backend API endpoints** for the Baytak Foundation Management system.

Currency across the app is fixed to **EGP** (Egyptian Pound).

---

## Contents

1. [Quick start & login](#1-quick-start--login)
2. [Admin dashboard UI](#2-admin-dashboard-ui)
3. [Database tables & fields](#3-database-tables--fields)
4. [Backend endpoints](#4-backend-endpoints)

---

## 1. Quick start & login

| Service | URL |
|---------|-----|
| Public site + admin UI | http://localhost:8080 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/health |
| Prometheus metrics | http://localhost:8000/metrics |
| API docs (Swagger) | http://localhost:8000/docs |

### Default bootstrap admin

Created automatically on backend startup if missing (from `.env`):

| Field | Default |
|-------|---------|
| Email | `admin@charity.local` |
| Password | `ChangeMe123!` |

Env keys: `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD`.

### Roles

| Role | Purpose |
|------|---------|
| `admin` | Full access (users, donation types, custody assign, audit) |
| `finance` | Financial ops, approvals, reports, dashboard |
| `staff` | Day-to-day donors, donations, warehouse, cases |
| `viewer` | Read-oriented access to many lists |

After login: **admin/finance** land on `/dashboard`; other roles land on `/donors`.

---

## 2. Admin dashboard UI

The staff app lives behind authentication (`/login`). The public marketing/donate site is at `/` and is separate from this dashboard.

### Sidebar navigation

| Tab | Path | Who sees it |
|-----|------|-------------|
| Overview | `/dashboard` | admin, finance |
| Donors | `/donors` | all authenticated |
| Donations | `/donations` | all authenticated |
| Donation types | `/donation-types` | admin, finance, viewer |
| Warehouse (المخزن) | `/warehouse` | all authenticated |
| Cases (الحالات) | `/cases` | all authenticated |
| Custody | `/custody` | all authenticated |
| Approvals | `/approvals` | admin, finance |
| Reports | `/reports` | admin, finance, viewer |
| Scheduled reports | `/reports/scheduled` | admin, finance |
| Users | `/users` | admin |
| Profile / settings | `/profile` | all authenticated |

Default language is **Arabic**; EN/AR can be switched from the top bar.

---

### Page-by-page

#### Overview (`/dashboard`)

Period KPIs and charts (`day` / `week` / `month`):

- Donations received, active donors, custody available, pending approvals
- Giving by fund (pie), donation distribution (bar)
- Recently active donors

Read-only; no create forms.

#### Donors (`/donors`)

Donor CRM.

| Action | Who |
|--------|-----|
| Create donor | authenticated |
| Search / filter (name, phone, ID) | authenticated |
| Edit / soft-delete | admin |

**Form fields:** first name, last name, primary phone, city, address, country.

#### Donations (`/donations`)

Income ledger (amounts in **EGP** only — no currency dropdown).

| Action | Who |
|--------|-----|
| Record donation | authenticated |
| Filter (donor, type, status, amount range, dates) | authenticated |
| Edit / cancel | admin, finance |

**Form fields:** donor, donation type, amount (EGP), received at, payment method, status (`confirmed` / `cancelled` / `refunded`), receipt number.

#### Donation types (`/donation-types`)

Fund / cause catalog.

| Action | Who |
|--------|-----|
| View list | admin, finance, viewer |
| Create / edit / deactivate | admin |

**Form fields:** fund name, description, active.

#### Warehouse (`/warehouse`) — المخزن

Inventory of supplies and materials.

| Action | Who |
|--------|-----|
| Add / edit / search / deactivate items | authenticated |

**Form fields:** item name, SKU, unit (default `piece`), quantity, location, notes, active.

#### Cases (`/cases`) — الحالات

Beneficiary / aid cases (medical, feeding, etc.).

| Action | Who |
|--------|-----|
| Add / edit / filter / cancel cases | authenticated |

**Form fields:** case number (auto if empty), beneficiary name, phone, category, status, priority, requested amount (EGP), approved amount (EGP), description.

**Statuses:** `open`, `in_progress`, `closed`, `cancelled`  
**Priorities:** `low`, `medium`, `high`, `urgent`

#### Custody (`/custody`)

Cash custody assignments and expense submission.

| Action | Who |
|--------|-----|
| Assign custody | admin |
| Edit assignment status/description | admin |
| Submit expense on active assignment | assignee |

**Assign fields:** recipient user, amount (EGP), assigned at, description  
**Expense fields:** title, amount (EGP), expense date, description  
**Assignment statuses:** `active`, `closed`, `cancelled`

#### Approvals (`/approvals`)

Review pending custody expenses.

| Action | Who |
|--------|-----|
| Approve / reject | admin, finance |

#### Reports (`/reports`)

Manual CSV export for a date window.

- Report types: donations, donors, custody
- Generate CSV, download history, link to scheduled reports

#### Scheduled reports (`/reports/scheduled`)

Recurring CSV generation + SMTP delivery.

**Form fields:** schedule name, report type, frequency (`weekly` / `monthly` / `yearly`), reporting window (`last_7_days` / `last_30_days` / `last_365_days`), email recipients, active.

Actions: create, edit, run now, disable.

#### Users (`/users`)

Team accounts (admin only).

**Form fields:** first/last name, email, phone, password (≥8), roles (`admin` / `finance` / `staff` / `viewer`).

#### Profile (`/profile`)

Own account: update name/phone; change password. Email is read-only.

---

## 3. Database tables & fields

ORM models live in `backend/app/models.py`. Migrations are under `backend/alembic/versions/`.

### Enums

| Enum | Values |
|------|--------|
| `donation_status` | `confirmed`, `cancelled`, `refunded` |
| `case_status` | `open`, `in_progress`, `closed`, `cancelled` |
| `case_priority` | `low`, `medium`, `high`, `urgent` |
| `custody_status` | `active`, `closed`, `cancelled` |
| `expense_status` | `pending`, `approved`, `rejected` |
| `report_type` | `donations`, `donors`, `custody` |
| `report_format` | `csv`, `pdf`, `excel` |
| `generated_report_status` | `pending`, `completed`, `failed` |

### Shared mixin

Most business tables include:

| Column | Type | Notes |
|--------|------|--------|
| `created_at` | timestamptz | default now |
| `updated_at` | timestamptz | default now, updated on change |

### Association

**`user_roles`** — many-to-many: `user_id` → `users.id`, `role_id` → `roles.id` (CASCADE).

---

### `users`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `first_name` | varchar(100) | |
| `last_name` | varchar(100) | |
| `phone_number` | varchar(50) | nullable |
| `email` | varchar(255) | unique, indexed |
| `password_hash` | varchar(255) | |
| `is_active` | boolean | default true |
| `created_at` / `updated_at` | timestamptz | |

### `roles`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `name` | varchar(50) | unique (`admin`, `finance`, `staff`, `viewer`) |
| `description` | varchar(255) | nullable |

### `refresh_tokens`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `token_jti` | varchar(64) | unique |
| `user_id` | FK → users | CASCADE |
| `expires_at` | timestamptz | |
| `revoked_at` | timestamptz | nullable |
| `created_at` | timestamptz | |

### `password_reset_tokens`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `token_jti` | varchar(64) | unique |
| `user_id` | FK → users | CASCADE |
| `expires_at` | timestamptz | |
| `used_at` | timestamptz | nullable |
| `created_at` | timestamptz | |

### `donors`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `first_name` / `last_name` | varchar(100) | indexed |
| `normalized_full_name` | varchar(205) | indexed |
| `is_deleted` | boolean | soft delete |
| `created_by_user_id` | FK → users | |
| `created_at` / `updated_at` | timestamptz | |

Related: `donor_phone_numbers`, `donor_addresses`, `donor_notes`.

### `donor_phone_numbers`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `donor_id` | FK → donors | CASCADE |
| `phone_number` | varchar(50) | |
| `is_primary` | boolean | |

### `donor_addresses`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `donor_id` | FK → donors | CASCADE |
| `address_line` | text | |
| `city` / `country` | varchar(100) | nullable |
| `is_primary` | boolean | |

### `donor_notes`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `donor_id` | FK → donors | CASCADE |
| `note` | text | |
| `created_by_user_id` | FK → users | |
| `created_at` | timestamptz | |

### `donation_types`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `type_name` | varchar(100) | unique |
| `description` | text | nullable |
| `is_active` | boolean | default true |
| `created_at` / `updated_at` | timestamptz | |

### `donations`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `donor_id` | FK → donors | indexed |
| `donation_type_id` | FK → donation_types | indexed |
| `amount` | numeric(14,2) | indexed |
| `currency` | varchar(3) | default **`EGP`** |
| `donation_date` | timestamptz | indexed |
| `payment_method` | varchar(100) | nullable |
| `receipt_number` | varchar(100) | unique, nullable |
| `status` | enum `donation_status` | default `confirmed` |
| `created_by_user_id` | FK → users | |
| `created_at` / `updated_at` | timestamptz | |

Index: `(donation_type_id, donation_date)`.

### `donation_notes`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `donation_id` | FK → donations | CASCADE |
| `note` | text | |
| `created_by_user_id` | FK → users | |
| `created_at` | timestamptz | |

### `custody_assignments`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `user_id` | FK → users | recipient |
| `amount` | numeric(14,2) | |
| `assigned_by_user_id` | FK → users | |
| `assigned_at` | timestamptz | |
| `description` | text | nullable |
| `status` | enum `custody_status` | default `active` |
| `created_at` / `updated_at` | timestamptz | |

### `custody_expenses`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `custody_assignment_id` | FK → custody_assignments | |
| `user_id` | FK → users | |
| `title` | varchar(255) | |
| `description` | text | nullable |
| `amount` | numeric(14,2) | |
| `expense_date` | timestamptz | |
| `status` | enum `expense_status` | default `pending` |
| `submitted_at` | timestamptz | |
| `created_at` / `updated_at` | timestamptz | |

### `custody_expense_approvals`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `custody_expense_id` | FK → custody_expenses | CASCADE |
| `approved_by_user_id` | FK → users | |
| `decision` | enum (expense status) | approve/reject |
| `comment` | text | nullable |
| `decided_at` | timestamptz | |

### `warehouse_items`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `name` | varchar(150) | indexed |
| `sku` | varchar(80) | unique, nullable |
| `quantity` | numeric(14,2) | default 0 |
| `unit` | varchar(40) | default `piece` |
| `location` | varchar(150) | nullable |
| `notes` | text | nullable |
| `is_active` | boolean | default true |
| `created_at` / `updated_at` | timestamptz | |

### `aid_cases`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `case_number` | varchar(50) | unique |
| `beneficiary_name` | varchar(200) | indexed |
| `phone` | varchar(50) | nullable |
| `category` | varchar(100) | indexed |
| `status` | enum `case_status` | default `open` |
| `priority` | enum `case_priority` | default `medium` |
| `description` | text | nullable |
| `requested_amount` | numeric(14,2) | nullable (EGP) |
| `approved_amount` | numeric(14,2) | nullable (EGP) |
| `created_by_user_id` | FK → users | |
| `assigned_user_id` | FK → users | nullable |
| `created_at` / `updated_at` | timestamptz | |

### `scheduled_reports`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `name` | varchar(255) | |
| `report_type` | enum `report_type` | |
| `frequency` | varchar(30) | |
| `cron_expression` | varchar(100) | nullable |
| `filters_json` | json | e.g. reporting window |
| `recipients_json` | json | email list |
| `format` | enum `report_format` | |
| `is_active` | boolean | |
| `last_run_at` / `next_run_at` | timestamptz | nullable |
| `created_by_user_id` | FK → users | |
| `created_at` / `updated_at` | timestamptz | |

### `generated_reports`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `scheduled_report_id` | FK | nullable |
| `report_type` | enum | |
| `file_path` | varchar(500) | nullable |
| `format` | enum | |
| `generated_by_user_id` | FK → users | nullable |
| `generated_at` | timestamptz | |
| `status` | enum `generated_report_status` | |
| `error_message` | text | nullable |

### `audit_logs`

| Column | Type | Notes |
|--------|------|--------|
| `id` | int PK | |
| `actor_user_id` | FK → users | nullable |
| `action` | varchar(100) | indexed |
| `entity_type` | varchar(100) | indexed |
| `entity_id` | varchar(100) | indexed |
| `old_value_json` / `new_value_json` | json | nullable |
| `ip_address` | varchar(64) | nullable |
| `user_agent` | varchar(512) | nullable |
| `created_at` | timestamptz | |

---

## 4. Backend endpoints

Base API prefix: **`/api/v1`**.

Auth:

- **Public** — no token
- **CurrentUser** — valid JWT (any active role)
- **Admin** — role `admin`
- **FinanceOrAdmin** — role `admin` or `finance`

Interactive docs: http://localhost:8000/docs

---

### Ops

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/health` | Public | Liveness |
| GET | `/metrics` | Public | Prometheus scrape |

---

### Auth — `/api/v1/auth`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/auth/login` | Public | Login → access + refresh tokens |
| POST | `/auth/refresh` | Public | Refresh access token |
| POST | `/auth/logout` | CurrentUser | Revoke refresh token |
| POST | `/auth/forgot-password` | Public | Request reset |
| POST | `/auth/reset-password` | Public | Reset with token |
| POST | `/auth/change-password` | CurrentUser | Change own password |

---

### Profile — `/api/v1/profile`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/profile` | CurrentUser | Current user |
| PATCH | `/profile` | CurrentUser | Update name/phone |
| GET | `/profile/custody` | CurrentUser | Own custody assignments |
| GET | `/profile/custody-expenses` | CurrentUser | Own expenses |
| POST | `/profile/custody-expenses` | CurrentUser | Submit expense |

---

### Users — `/api/v1/users`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/users` | Admin | List users |
| POST | `/users` | Admin | Create user |
| GET | `/users/roles` | Admin | List roles |
| GET | `/users/{user_id}` | Admin | Get user |
| PATCH | `/users/{user_id}` | Admin | Update user |
| POST | `/users/{user_id}/roles` | Admin | Set roles |
| DELETE | `/users/{user_id}/roles/{role_id}` | Admin | Remove role |
| POST | `/users/{user_id}/disable` | Admin | Disable user |
| POST | `/users/{user_id}/reset-password` | Admin | Admin password reset |

---

### Donors — `/api/v1/donors`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/donors` | CurrentUser | List / filter / paginate |
| POST | `/donors` | CurrentUser | Create |
| GET | `/donors/{donor_id}` | CurrentUser | Get |
| PATCH | `/donors/{donor_id}` | CurrentUser | Update |
| DELETE | `/donors/{donor_id}` | Admin | Soft-delete |
| POST | `/donors/{donor_id}/notes` | CurrentUser | Add note |
| GET | `/donors/{donor_id}/donations` | CurrentUser | Donor donations |

---

### Donation types — `/api/v1/donation-types`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/donation-types` | CurrentUser | List |
| POST | `/donation-types` | Admin | Create |
| GET | `/donation-types/{id}` | CurrentUser | Get |
| PATCH | `/donation-types/{id}` | Admin | Update |
| DELETE | `/donation-types/{id}` | Admin | Deactivate |

---

### Donations — `/api/v1/donations`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/donations` | CurrentUser | List / filter |
| POST | `/donations` | CurrentUser | Create (currency forced to EGP) |
| GET | `/donations/{id}` | CurrentUser | Get |
| PATCH | `/donations/{id}` | FinanceOrAdmin | Update |
| DELETE | `/donations/{id}` | FinanceOrAdmin | Cancel |
| POST | `/donations/{id}/notes` | CurrentUser | Add note |

---

### Warehouse — `/api/v1/warehouse`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/warehouse` | CurrentUser | List |
| POST | `/warehouse` | CurrentUser | Create |
| GET | `/warehouse/{id}` | CurrentUser | Get |
| PATCH | `/warehouse/{id}` | CurrentUser | Update |
| DELETE | `/warehouse/{id}` | CurrentUser | Deactivate |

---

### Cases — `/api/v1/cases`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/cases` | CurrentUser | List / filter / paginate |
| POST | `/cases` | CurrentUser | Create |
| GET | `/cases/{id}` | CurrentUser | Get |
| PATCH | `/cases/{id}` | CurrentUser | Update |
| DELETE | `/cases/{id}` | CurrentUser | Cancel |

---

### Custody — `/api/v1/custody`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/custody` | FinanceOrAdmin | List assignments |
| POST | `/custody` | Admin | Assign custody |
| GET | `/custody/{id}` | CurrentUser | Get (own or elevated) |
| PATCH | `/custody/{id}` | Admin | Update |
| GET | `/custody/{id}/expenses` | CurrentUser | List expenses |
| POST | `/custody/{id}/expenses` | CurrentUser | Submit expense |
| GET | `/custody/users/{user_id}/summary` | FinanceOrAdmin | User custody summary |

---

### Approvals — `/api/v1/approvals`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/approvals/custody-expenses` | FinanceOrAdmin | Pending expenses |
| POST | `/approvals/custody-expenses/{id}/approve` | FinanceOrAdmin | Approve |
| POST | `/approvals/custody-expenses/{id}/reject` | FinanceOrAdmin | Reject |

---

### Dashboard — `/api/v1/dashboard`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/dashboard/summary` | FinanceOrAdmin | Period KPIs |
| GET | `/dashboard/donations-by-type` | FinanceOrAdmin | Totals by fund |
| GET | `/dashboard/recent-donors` | FinanceOrAdmin | Recent donors |
| GET | `/dashboard/custody-summary` | FinanceOrAdmin | Custody totals |

Query: `period=day|week|month` where applicable.

---

### Reports — `/api/v1/reports`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/reports/donations` | FinanceOrAdmin | Donation report rows |
| GET | `/reports/donors` | FinanceOrAdmin | Donor report rows |
| GET | `/reports/custody` | FinanceOrAdmin | Custody report rows |
| POST | `/reports/generate` | FinanceOrAdmin | Generate file |
| GET | `/reports/generated` | FinanceOrAdmin | List generated files |
| GET | `/reports/generated/{id}/download` | FinanceOrAdmin | Download |

---

### Scheduled reports — `/api/v1/scheduled-reports`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/scheduled-reports` | FinanceOrAdmin | List |
| POST | `/scheduled-reports` | FinanceOrAdmin | Create |
| PATCH | `/scheduled-reports/{id}` | FinanceOrAdmin | Update |
| DELETE | `/scheduled-reports/{id}` | FinanceOrAdmin | Disable |
| POST | `/scheduled-reports/{id}/run` | FinanceOrAdmin | Run now (+ SMTP) |

---

### Audit — `/api/v1/audit-logs`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/audit-logs` | Admin | List audit events (filter by action, entity, actor, dates) |

There is no dedicated audit UI page yet; use API / Swagger or future admin screen.

---

## Related files

| Area | Path |
|------|------|
| Admin routes | `frontend/src/App.tsx` |
| Sidebar | `frontend/src/components/AppShell.tsx` |
| Admin pages | `frontend/src/pages.tsx` |
| Models | `backend/app/models.py` |
| Schemas | `backend/app/schemas.py` |
| Routers | `backend/app/routers/` |
| App entry | `backend/app/main.py` |
| Compose | `compose.yaml` |
| Env example | `.env.example` |
