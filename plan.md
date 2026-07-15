## 1. Executive Summary

You are building a **Donation Charity Management System** with:

1. **Public Landing Page**
   - Explains the organization, mission, activities, contact information, and possibly donation instructions.

2. **Admin Dashboard**
   - Internal system for managing donors, donations, donation types, custody funds, users, approvals, reports, and user profiles.

The system will be hosted on:

- **Single EC2 instance running k3s**
- **Separate Jenkins server**
- **PostgreSQL database**
- **Python backend using SQLAlchemy**
- **Modern frontend with strong UI**
- **Docker images stored in private Docker Hub repo**
- **Deployment using Helm**
- **Infrastructure provisioned with Terraform**
- **Server configuration managed by Ansible**
- **Monitoring with Prometheus and Grafana**

Recommended core stack:

| Layer | Recommendation |
|---|---|
| Frontend | React + TypeScript + Vite or Next.js |
| Backend | FastAPI + SQLAlchemy + Alembic |
| Database | PostgreSQL |
| Auth | JWT access/refresh tokens, role-based access control |
| Background Jobs | Celery or RQ with Redis |
| Reports | Backend-generated CSV/PDF + chart data APIs |
| Email | SMTP provider or AWS SES |
| Runtime | k3s with containerd recommended; Docker runtime possible but not ideal |
| CI/CD | Jenkins pipeline |
| Deployment | Helm charts |
| Monitoring | Prometheus, Grafana, Alertmanager |
| Logging | Loki + Promtail recommended |

---

# 2. Requirements Analysis

## 2.1 Functional Requirements

### Public Landing Page

The landing page should include:

- Organization name and branding
- Mission and vision
- About section
- Charity activities/projects
- Contact information
- Optional: public donation instructions
- Optional: public donation form in future
- Responsive design for mobile and desktop

### Admin Dashboard

The dashboard must include these modules:

---

## A. Home / Statistics

Features:

- Show donation totals by donation type.
- Period selector:
  - Daily
  - Weekly
  - Monthly
  - Custom date range recommended
- Show total number of donors.
- Show latest active donors for selected period.
- Show total custody amount.
- Show pending custody expenses count.
- Show total donations amount.
- Show recent donations.

Important statistics:

- Donations by type
- Donations by date
- Donor activity
- Custody balance
- Approved vs pending expenses

---

## B. Donors

Features:

- Add new donor.
- Edit donor.
- Search/filter donors by:
  - Name
  - Phone number
  - ID
- View donor profile.
- View donor donation history.

Minimum donor fields:

- ID
- First name
- Last name
- Phone numbers list
- Addresses list
- Notes list
- Total amount donated
- Last donation type
- Created date
- Updated date

Recommended improvement:

Do **not** store `total_amount_donated` and `last_donation_type` as manually updated fields only. They should be calculated from donations or maintained through controlled backend logic to avoid inconsistent data.

---

## C. Donations

Features:

- Add new donation.
- Edit donation.
- Search/filter donations by:
  - Amount
  - Type
  - Date/time range
  - Donor
- View donation details.

Minimum donation fields:

- ID
- Amount
- Donor ID
- Donation type
- Donation date
- Notes list
- Created by user
- Created date
- Updated date

Recommended fields:

- Payment method
- Receipt number
- Status: confirmed, cancelled, refunded
- Currency

---

## D. Donation Types

Features:

- Add donation type.
- Edit donation type.
- Search/filter donation types by:
  - ID
  - Type name

Minimum fields:

- ID
- Type name
- Description
- Active/inactive flag

Examples:

- Zakat
- Sadaqah
- Orphans
- Food aid
- Emergency relief
- Medical support

---

## E. Custody

Custody means money assigned to a user for expenses.

Features:

- Admin can add custody to a user.
- Search/filter custody by:
  - User
  - Date
  - Amount
- View all custody records.
- View custody balance per user.
- Track expenses against assigned custody.
- Finance/admin approval workflow.

Custody lifecycle:

1. Admin assigns custody to user.
2. User sees custody in profile.
3. User submits expense.
4. Expense remains pending.
5. Finance/admin approves or rejects expense.
6. If approved, custody remaining balance decreases.
7. If rejected, custody balance remains unchanged.

Important design decision:

Custody should be modeled as a ledger, not just a single mutable balance field. This prevents accounting errors.

---

## F. Reports

Features:

- Generate donor reports.
- Generate donation reports.
- Generate custody reports recommended.
- Display reports using:
  - Tables
  - Pie charts
  - Bar charts
  - Line charts
- Download reports as:
  - CSV
  - PDF
  - Excel optional
- Filter by date range.
- Filter by donation type.
- Filter by donor.
- Schedule automatic reports:
  - Weekly
  - Monthly
  - Yearly
  - Custom interval recommended
- Send scheduled reports by email.

Scheduled report fields:

- Report type
- Frequency
- Recipients
- Filters
- Format
- Active/inactive
- Last run date
- Next run date

---

## G. Profile

Features:

- User can update:
  - Name
  - Phone number
  - Password
- User can see assigned custody.
- User can add expenses.
- User can see expense approval status:
  - Pending
  - Approved
  - Rejected

Example:

- Admin assigns 20,000 custody to Ali.
- Ali adds expense: “buy documents”, 5,000.
- Expense is pending.
- After finance approval, custody available balance becomes 15,000.

---

## H. Users

Visible to admin only.

Features:

- Add user.
- Edit user.
- Disable user.
- Assign role.
- Reset password.
- View all custody assigned to all users.
- View user activity.

Roles:

- Admin
- Finance
- Staff/User
- Viewer optional

---

## I. Approval

Visible to admin and finance.

Features:

- View pending custody expenses.
- Approve expense.
- Reject expense.
- Add approval/rejection comment.
- Track approver and approval timestamp.

---

# 3. Non-Functional Requirements

## Performance

Initial target:

- 10-50 internal users
- 1,000-100,000 donors
- 10,000-1,000,000 donations over time

Performance goals:

- Dashboard loads in less than 3 seconds for common date ranges.
- Search returns within 1 second for indexed fields.
- Reports under 10,000 rows generate quickly.
- Large reports should be generated asynchronously.

## Availability

Current requirement uses a single EC2 instance, so availability is limited.

Expected availability:

- Acceptable for small organization.
- Not highly available.
- Downtime possible during EC2 failure, disk failure, or maintenance.

Recommended future improvement:

- Move PostgreSQL to Amazon RDS.
- Use multiple k3s nodes or EKS.
- Use S3 for backups and generated reports.
- Use load balancer.

## Security

Required:

- Authentication
- Role-based authorization
- Password hashing
- HTTPS
- Database backups
- Audit logging
- Secrets management
- Input validation
- Rate limiting
- Secure Jenkins credentials

## Maintainability

Required:

- Clean architecture
- Database migrations
- Automated CI/CD
- Automated tests
- Monitoring and alerts
- Documentation

---

# 4. Recommended Architecture

## 4.1 High-Level Architecture Diagram

```text
                         Internet Users
                              |
                              v
                    +--------------------+
                    |   Domain / DNS     |
                    +--------------------+
                              |
                              v
                    +--------------------+
                    |  k3s EC2 Instance  |
                    |--------------------|
                    |  Ingress NGINX     |
                    |  Cert-Manager      |
                    |--------------------|
                    |  Frontend App      |
                    |  Backend API       |
                    |  Worker Service    |
                    |  Redis             |
                    |  PostgreSQL        |
                    |  Prometheus        |
                    |  Grafana           |
                    |  Loki/Promtail     |
                    +--------------------+
                              |
                              v
                    +--------------------+
                    |  Backup Storage    |
                    |  S3 recommended    |
                    +--------------------+


                    +--------------------+
                    | Jenkins EC2 Server |
                    |--------------------|
                    | Watches Git Repo   |
                    | Builds Images      |
                    | Pushes Docker Hub  |
                    | Runs Helm Upgrade  |
                    +--------------------+
```

---

## 4.2 Application Architecture

```text
+-----------------------+
| Public Landing Page   |
| React/Next.js         |
+-----------+-----------+
            |
            v
+-----------------------+
| Admin Dashboard       |
| React + TypeScript    |
| Component Library     |
+-----------+-----------+
            |
            v
+-----------------------+
| Backend API           |
| FastAPI               |
| SQLAlchemy            |
| Alembic Migrations    |
+-----------+-----------+
            |
            +----------------------+
            |                      |
            v                      v
+-------------------+      +----------------------+
| PostgreSQL        |      | Redis                |
| Main database     |      | Jobs/cache/queue     |
+-------------------+      +----------+-----------+
                                      |
                                      v
                           +----------------------+
                           | Worker Service       |
                           | Reports/emails/jobs  |
                           +----------------------+
```

---

## 4.3 Backend Internal Architecture

Recommended backend layers:

```text
API Layer
  |
  v
Service Layer
  |
  v
Repository/Data Access Layer
  |
  v
SQLAlchemy Models
  |
  v
PostgreSQL
```

Responsibilities:

| Layer | Responsibility |
|---|---|
| API Layer | HTTP endpoints, request validation, response formatting |
| Service Layer | Business rules, custody logic, approval workflow |
| Repository Layer | Database queries |
| Models | SQLAlchemy table mappings |
| Background Jobs | Scheduled reports, email sending, heavy exports |

---

# 5. Technology Choices

## 5.1 Backend

Recommended:

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic
- PostgreSQL driver
- JWT authentication
- Celery or RQ for background jobs
- Redis for queue/cache
- WeasyPrint or ReportLab for PDF reports
- Pandas/OpenPyXL optional for Excel exports

Why FastAPI?

- Modern Python
- High performance
- Great validation
- Automatic API documentation
- Works well with SQLAlchemy

---

## 5.2 Frontend

Recommended:

- React + TypeScript
- Vite for admin dashboard
- Tailwind CSS or Material UI
- TanStack Query for API data fetching
- React Hook Form for forms
- Zod or Yup for validation
- Recharts, Chart.js, or ECharts for charts

Alternative:

- Next.js if you want SEO-friendly public landing page and integrated frontend routing.

Recommended option:

```text
React + TypeScript + Vite for admin dashboard
Static public landing page served by same frontend app
```

This is simpler for a small deployment.

---

## 5.3 Database

Recommended:

- PostgreSQL 16
- StatefulSet in k3s for now
- Persistent volume on EC2 EBS
- Automated backups to S3

Important challenge:

Running PostgreSQL inside a single-node k3s cluster is simple but risky. If the EC2 instance fails, the app and database both go down. For production, Amazon RDS would be safer.

---

## 5.4 Container Runtime

You requested Docker runtime.

Important challenge:

Modern k3s uses `containerd` by default. Docker runtime support requires additional configuration using `cri-dockerd`, and it adds complexity. Kubernetes removed direct Docker runtime support years ago.

Recommendation:

- Use Docker for building images in Jenkins.
- Use k3s default `containerd` for running containers.

If Docker runtime is mandatory:

- Install Docker.
- Install cri-dockerd.
- Configure k3s to use Docker through CRI.

However, this is not recommended unless there is a strong reason.

---

# 6. Database Design

## 6.1 Main Entities

Core tables:

1. users
2. roles
3. user_roles
4. donors
5. donor_phone_numbers
6. donor_addresses
7. donor_notes
8. donation_types
9. donations
10. donation_notes
11. custody_assignments
12. custody_expenses
13. custody_expense_approvals
14. scheduled_reports
15. generated_reports
16. audit_logs
17. refresh_tokens/password_reset_tokens optional

---

## 6.2 Table Design

### users

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| first_name | string | Required |
| last_name | string | Required |
| phone_number | string | Optional |
| email | string | Unique, recommended |
| password_hash | string | Required |
| is_active | boolean | Default true |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

---

### roles

| Field | Type | Notes |
|---|---|---|
| id | int | Primary key |
| name | string | admin, finance, staff, viewer |
| description | text | Optional |

---

### user_roles

| Field | Type | Notes |
|---|---|---|
| user_id | FK | users.id |
| role_id | FK | roles.id |

Composite unique:

```text
(user_id, role_id)
```

---

### donors

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| first_name | string | Required |
| last_name | string | Required |
| normalized_full_name | string | For searching |
| total_amount_donated | numeric | Cached, optional |
| last_donation_type_id | FK | Optional cached field |
| last_donation_at | timestamp | Optional cached field |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |
| created_by_user_id | FK | users.id |

Recommendation:

Use cached donor totals only if maintained transactionally by backend logic. Otherwise, calculate from donations.

---

### donor_phone_numbers

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| donor_id | FK | donors.id |
| phone_number | string | Required |
| is_primary | boolean | Default false |

Indexes:

- phone_number
- donor_id

---

### donor_addresses

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| donor_id | FK | donors.id |
| address_line | text | Required |
| city | string | Optional |
| country | string | Optional |
| is_primary | boolean | Default false |

---

### donor_notes

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| donor_id | FK | donors.id |
| note | text | Required |
| created_by_user_id | FK | users.id |
| created_at | timestamp | Required |

---

### donation_types

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| type_name | string | Unique |
| description | text | Optional |
| is_active | boolean | Default true |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

---

### donations

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| donor_id | FK | donors.id |
| donation_type_id | FK | donation_types.id |
| amount | numeric | Required, greater than 0 |
| currency | string | Default local currency |
| donation_date | timestamp | Required |
| payment_method | string | Optional |
| receipt_number | string | Optional, unique |
| status | enum | confirmed, cancelled |
| created_by_user_id | FK | users.id |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

Indexes:

- donor_id
- donation_type_id
- donation_date
- amount
- status
- combined index: donation_type_id + donation_date

---

### donation_notes

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| donation_id | FK | donations.id |
| note | text | Required |
| created_by_user_id | FK | users.id |
| created_at | timestamp | Required |

---

### custody_assignments

Represents money assigned by admin to user.

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| user_id | FK | users.id |
| amount | numeric | Required |
| assigned_by_user_id | FK | users.id |
| assigned_at | timestamp | Required |
| description | text | Optional |
| status | enum | active, closed, cancelled |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

---

### custody_expenses

Represents expenses submitted by users.

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| custody_assignment_id | FK | custody_assignments.id |
| user_id | FK | users.id |
| title | string | Required |
| description | text | Optional |
| amount | numeric | Required |
| expense_date | timestamp | Required |
| status | enum | pending, approved, rejected |
| submitted_at | timestamp | Required |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

Important rule:

Only approved expenses reduce available custody balance.

Available balance formula:

```text
custody assignment amount - sum(approved expenses)
```

---

### custody_expense_approvals

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| custody_expense_id | FK | custody_expenses.id |
| approved_by_user_id | FK | users.id |
| decision | enum | approved, rejected |
| comment | text | Optional |
| decided_at | timestamp | Required |

---

### scheduled_reports

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| name | string | Required |
| report_type | enum | donations, donors, custody |
| frequency | enum | weekly, monthly, yearly, custom |
| cron_expression | string | Optional |
| filters_json | jsonb | Report filters |
| recipients_json | jsonb | Email recipients |
| format | enum | pdf, csv, excel |
| is_active | boolean | Default true |
| last_run_at | timestamp | Optional |
| next_run_at | timestamp | Optional |
| created_by_user_id | FK | users.id |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

---

### generated_reports

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| scheduled_report_id | FK | nullable |
| report_type | enum | donations, donors, custody |
| file_path | string | Local/S3 path |
| format | enum | pdf, csv, excel |
| generated_by_user_id | FK | nullable |
| generated_at | timestamp | Required |
| status | enum | pending, completed, failed |
| error_message | text | Optional |

---

### audit_logs

| Field | Type | Notes |
|---|---|---|
| id | UUID/int | Primary key |
| actor_user_id | FK | users.id |
| action | string | Example: DONATION_CREATED |
| entity_type | string | donation, donor, user |
| entity_id | string | ID of affected record |
| old_value_json | jsonb | Optional |
| new_value_json | jsonb | Optional |
| ip_address | string | Optional |
| user_agent | string | Optional |
| created_at | timestamp | Required |

---

## 6.3 Database Relationships

```text
users 1----N donors
users 1----N donations
users N----N roles

donors 1----N donor_phone_numbers
donors 1----N donor_addresses
donors 1----N donor_notes
donors 1----N donations

donation_types 1----N donations
donations 1----N donation_notes

users 1----N custody_assignments
custody_assignments 1----N custody_expenses
custody_expenses 1----N custody_expense_approvals

users 1----N scheduled_reports
scheduled_reports 1----N generated_reports
```

---

# 7. API Design

Base API prefix:

```text
/api/v1
```

## 7.1 Authentication

| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | /auth/login | Login | Public |
| POST | /auth/refresh | Refresh access token | Authenticated |
| POST | /auth/logout | Logout | Authenticated |
| POST | /auth/change-password | Change own password | Authenticated |
| POST | /auth/forgot-password | Optional | Public |
| POST | /auth/reset-password | Optional | Public |

---

## 7.2 Profile

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | /profile | Get current user profile | Authenticated |
| PATCH | /profile | Update current user profile | Authenticated |
| GET | /profile/custody | View own custody | Authenticated |
| GET | /profile/custody-expenses | View own expenses | Authenticated |
| POST | /profile/custody-expenses | Submit expense | Authenticated |

---

## 7.3 Dashboard/Home Statistics

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | /dashboard/summary | Main dashboard summary | Admin/Finance |
| GET | /dashboard/donations-by-type | Donation amount/count by type | Admin/Finance |
| GET | /dashboard/recent-donors | Recently active donors | Admin/Finance |
| GET | /dashboard/custody-summary | Custody totals | Admin/Finance |

Common query parameters:

```text
period=day/week/month
start_date=
end_date=
```

---

## 7.4 Donors

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | /donors | Search/list donors | Authenticated |
| POST | /donors | Create donor | Authenticated |
| GET | /donors/{id} | Get donor details | Authenticated |
| PATCH | /donors/{id} | Update donor | Authenticated |
| DELETE | /donors/{id} | Soft delete donor | Admin |
| GET | /donors/{id}/donations | Donor donation history | Authenticated |
| POST | /donors/{id}/notes | Add donor note | Authenticated |

Search query examples:

```text
?name=ali
?phone=077
?id=123
?page=1&page_size=20
```

---

## 7.5 Donations

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | /donations | Search/list donations | Authenticated |
| POST | /donations | Create donation | Authenticated |
| GET | /donations/{id} | Get donation details | Authenticated |
| PATCH | /donations/{id} | Update donation | Admin/Finance |
| DELETE | /donations/{id} | Cancel/soft delete donation | Admin/Finance |
| POST | /donations/{id}/notes | Add donation note | Authenticated |

Search filters:

```text
amount_min=
amount_max=
donation_type_id=
donor_id=
start_date=
end_date=
status=
```

---

## 7.6 Donation Types

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | /donation-types | List/search types | Authenticated |
| POST | /donation-types | Create type | Admin |
| GET | /donation-types/{id} | Get type | Authenticated |
| PATCH | /donation-types/{id} | Update type | Admin |
| DELETE | /donation-types/{id} | Deactivate type | Admin |

---

## 7.7 Custody

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | /custody | List/search custody assignments | Admin/Finance |
| POST | /custody | Assign custody to user | Admin |
| GET | /custody/{id} | Custody details | Admin/Finance/Owner |
| PATCH | /custody/{id} | Update custody metadata | Admin |
| GET | /custody/{id}/expenses | List expenses for custody | Admin/Finance/Owner |
| POST | /custody/{id}/expenses | Submit expense | Owner |
| GET | /custody/users/{user_id}/summary | User custody summary | Admin/Finance |

---

## 7.8 Approvals

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | /approvals/custody-expenses | List pending expenses | Admin/Finance |
| POST | /approvals/custody-expenses/{id}/approve | Approve expense | Admin/Finance |
| POST | /approvals/custody-expenses/{id}/reject | Reject expense | Admin/Finance |

---

## 7.9 Users

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | /users | List/search users | Admin |
| POST | /users | Create user | Admin |
| GET | /users/{id} | Get user details | Admin |
| PATCH | /users/{id} | Update user | Admin |
| POST | /users/{id}/roles | Assign roles | Admin |
| DELETE | /users/{id}/roles/{role_id} | Remove role | Admin |
| POST | /users/{id}/disable | Disable user | Admin |
| POST | /users/{id}/reset-password | Reset password | Admin |

---

## 7.10 Reports

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | /reports/donations | Donation report data | Admin/Finance |
| GET | /reports/donors | Donor report data | Admin/Finance |
| GET | /reports/custody | Custody report data | Admin/Finance |
| POST | /reports/generate | Generate downloadable report | Admin/Finance |
| GET | /reports/generated | List generated reports | Admin/Finance |
| GET | /reports/generated/{id}/download | Download report | Admin/Finance |
| GET | /scheduled-reports | List scheduled reports | Admin/Finance |
| POST | /scheduled-reports | Create scheduled report | Admin/Finance |
| PATCH | /scheduled-reports/{id} | Update scheduled report | Admin/Finance |
| DELETE | /scheduled-reports/{id} | Disable scheduled report | Admin/Finance |

---

## 7.11 Audit Logs

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | /audit-logs | Search audit logs | Admin |

---

# 8. Authorization Matrix

| Feature | Admin | Finance | Staff/User | Viewer |
|---|---:|---:|---:|---:|
| Dashboard | Yes | Yes | Limited | Read-only |
| Donors CRUD | Yes | Yes | Create/read/update limited | Read-only |
| Donations CRUD | Yes | Yes | Create/read | Read-only |
| Donation Types | Yes | Read | No | Read |
| Assign Custody | Yes | No/Optional | No | No |
| Submit Expense | Yes | Yes | Yes, own only | No |
| Approve Expense | Yes | Yes | No | No |
| Reports | Yes | Yes | No/limited | Read-only |
| Users Management | Yes | No | No | No |
| Audit Logs | Yes | No/Optional | No | No |

---

# 9. Frontend Plan

## 9.1 Application Pages

### Public

- `/`
  - Landing page
- `/about`
  - Optional
- `/contact`
  - Optional

### Auth

- `/login`
- `/forgot-password`
- `/reset-password`

### Admin Dashboard

- `/dashboard`
- `/donors`
- `/donors/new`
- `/donors/:id`
- `/donations`
- `/donations/new`
- `/donation-types`
- `/custody`
- `/custody/:id`
- `/reports`
- `/reports/scheduled`
- `/profile`
- `/users`
- `/approvals`

---

## 9.2 UI Components

Required reusable components:

- Layout/sidebar
- Top navigation
- Role-based menu rendering
- Data table
- Search filters
- Date range picker
- Chart components
- Form components
- Modal dialog
- Confirmation dialog
- Notification/toast
- Pagination
- Loading skeleton
- Error state
- Empty state

---

## 9.3 Dashboard UX

Recommended widgets:

```text
+---------------------------------------------------+
| Total Donations | Total Donors | Custody Balance  |
+---------------------------------------------------+
| Donations by Type Pie Chart                       |
+---------------------------------------------------+
| Donations Over Time Line Chart                    |
+---------------------------------------------------+
| Recent Active Donors | Pending Approvals          |
+---------------------------------------------------+
```

---

# 10. Infrastructure Plan

## 10.1 AWS Infrastructure

You will need:

### Application Server

- EC2 instance
- Ubuntu 22.04 or 24.04 LTS
- Recommended size:
  - Minimum: t3.medium
  - Better: t3.large
- EBS volume:
  - Minimum 50 GB
  - Recommended 100-200 GB depending on reports and DB growth
- Elastic IP
- Security group
- IAM role for S3 backups
- DNS record

### Jenkins Server

- Separate EC2 instance
- Recommended size:
  - t3.small for small project
  - t3.medium if builds are heavy
- EBS volume:
  - 50-100 GB
- Docker installed for image builds
- Jenkins installed
- Access to:
  - Git repository
  - Docker Hub
  - k3s cluster through restricted kubeconfig
  - Helm

### S3 Bucket Recommended

Use S3 for:

- PostgreSQL backups
- Generated report files
- Optional frontend assets
- Disaster recovery

### Route 53 Optional

Use Route 53 if AWS manages DNS.

---

# 11. Terraform Plan

## 11.1 Terraform Modules

Recommended module structure:

```text
terraform/
  environments/
    dev/
    prod/
  modules/
    network/
    security-groups/
    ec2-app/
    ec2-jenkins/
    iam/
    s3-backups/
    dns/
```

---

## 11.2 Modules Description

### network module

Responsibilities:

- VPC
- Public subnet
- Internet gateway
- Route table
- Optional private subnet for future

For a simple setup, default VPC can be used, but custom VPC is cleaner.

---

### security-groups module

Security groups:

#### App server SG

Allow inbound:

| Port | Source | Purpose |
|---|---|---|
| 22 | Admin IP only | SSH |
| 80 | 0.0.0.0/0 | HTTP redirect |
| 443 | 0.0.0.0/0 | HTTPS |
| 6443 | Jenkins SG only | k3s API, if Jenkins needs direct cluster access |
| 3000/8080 | Avoid public exposure | Internal only |

Allow outbound:

- Internet access for pulling images and packages

#### Jenkins SG

Allow inbound:

| Port | Source | Purpose |
|---|---|---|
| 22 | Admin IP only | SSH |
| 8080 | Admin IP/VPN only | Jenkins UI |

Allow outbound:

- Git provider
- Docker Hub
- App server k3s API

---

### ec2-app module

Creates:

- EC2 app instance
- Elastic IP
- EBS volume
- IAM instance profile
- Tags

---

### ec2-jenkins module

Creates:

- EC2 Jenkins instance
- Elastic IP optional
- EBS volume
- Security group attachment

---

### iam module

Creates:

- IAM role for app EC2
- S3 access policy for backup bucket
- Optional CloudWatch access

---

### s3-backups module

Creates:

- S3 bucket
- Versioning
- Lifecycle policy
- Encryption
- Block public access

---

### dns module

Creates:

- A record for application domain
- Optional Jenkins subdomain if needed, but Jenkins should ideally not be public

---

# 12. Ansible Configuration Plan

## 12.1 Ansible Inventory

Hosts:

```text
[app]
app-server

[jenkins]
jenkins-server
```

## 12.2 Ansible Roles

Recommended roles:

```text
ansible/
  roles/
    common/
    docker/
    k3s/
    helm/
    kubectl/
    jenkins/
    node-exporter/
    backup-tools/
    security-hardening/
```

---

## 12.3 App Server Configuration

Tasks:

1. Update packages.
2. Install security updates.
3. Configure timezone.
4. Create deploy user.
5. Configure SSH hardening.
6. Install Docker if mandatory.
7. Install k3s.
8. Install Helm.
9. Install kubectl.
10. Configure k3s kubeconfig.
11. Configure firewall.
12. Configure backup scripts/tools.
13. Configure log rotation.
14. Install node exporter optional if not using Kubernetes DaemonSet.

---

## 12.4 Jenkins Server Configuration

Tasks:

1. Update packages.
2. Install Java.
3. Install Jenkins.
4. Install Docker.
5. Install Git.
6. Install Helm.
7. Install kubectl.
8. Install Jenkins plugins:
   - Git
   - Pipeline
   - Docker Pipeline
   - Credentials
   - Blue Ocean optional
   - Slack/email notification optional
9. Add Jenkins user to Docker group.
10. Configure credentials:
   - Git token
   - Docker Hub credentials
   - Kubeconfig
   - Helm values secret access
11. Configure firewall.

---

# 13. Kubernetes/k3s Design

## 13.1 Namespaces

Recommended namespaces:

```text
charity-prod
monitoring
ingress
cert-manager
```

Optional:

```text
charity-dev
```

---

## 13.2 Helm Releases

Required Helm releases:

| Release | Namespace | Purpose |
|---|---|---|
| ingress-nginx | ingress | Ingress controller |
| cert-manager | cert-manager | TLS certificates |
| charity-app | charity-prod | Frontend, backend, worker |
| postgresql | charity-prod | Database |
| redis | charity-prod | Queue/cache |
| prometheus | monitoring | Metrics |
| grafana | monitoring | Dashboards |
| loki/promtail | monitoring | Logs, recommended |

---

## 13.3 Application Kubernetes Resources

For the application Helm chart:

### Frontend

- Deployment
- Service
- Ingress route
- ConfigMap for public env vars
- Resource requests/limits
- HorizontalPodAutoscaler optional

### Backend API

- Deployment
- Service
- Ingress route under `/api`
- Secret for DB credentials and JWT secret
- ConfigMap for non-secret settings
- Readiness probe
- Liveness probe
- Resource requests/limits

### Worker

- Deployment
- Secret/env from backend
- Connects to Redis and PostgreSQL
- Handles scheduled reports and emails

### PostgreSQL

- StatefulSet from Helm chart
- PersistentVolumeClaim
- Secret for password
- Backup CronJob

### Redis

- Deployment/StatefulSet
- Service
- PVC optional

### Migration Job

- Kubernetes Job run before backend deployment or as part of Helm upgrade.
- Applies database migrations.
- Must be idempotent.

### Backup CronJob

- Runs periodic PostgreSQL backups.
- Uploads to S3.
- Keeps retention policy.

---

## 13.4 Kubernetes Resource Diagram

```text
Namespace: charity-prod

+------------------+       +------------------+
| Frontend Pod(s)  | ----> | Backend API Pod  |
+------------------+       +---------+--------+
                                     |
                                     v
                           +---------+--------+
                           | PostgreSQL       |
                           | StatefulSet      |
                           +---------+--------+
                                     |
                                     v
                           +------------------+
                           | PVC / EBS        |
                           +------------------+

                           +------------------+
                           | Redis            |
                           +---------+--------+
                                     ^
                                     |
                           +---------+--------+
                           | Worker Pod       |
                           | Reports/Emails   |
                           +------------------+

+------------------+
| Ingress NGINX    |
+------------------+
```

---

# 14. Helm Chart Plan

## 14.1 Chart Structure

```text
helm/
  charity-app/
    Chart.yaml
    values.yaml
    values-dev.yaml
    values-prod.yaml
    templates/
      frontend-deployment
      frontend-service
      backend-deployment
      backend-service
      worker-deployment
      ingress
      configmap
      secrets
      migration-job
      serviceaccount
```

No code is included here, but this is the recommended structure.

---

## 14.2 Helm Values

Important configurable values:

- Image repository
- Image tag
- Replica count
- Environment variables
- Database connection
- Redis connection
- JWT settings
- Email settings
- Resource limits
- Ingress host
- TLS secret
- Feature flags

---

# 15. CI/CD Pipeline with Jenkins

## 15.1 Pipeline Overview

```text
Developer pushes code
        |
        v
Git repository webhook triggers Jenkins
        |
        v
Jenkins checkout
        |
        v
Run lint/tests
        |
        v
Build frontend image
Build backend image
        |
        v
Security scan images
        |
        v
Push images to Docker Hub private repo
        |
        v
Run Helm upgrade on k3s cluster
        |
        v
Run smoke tests
        |
        v
Notify team
```

---

## 15.2 Jenkins Pipeline Stages

1. Checkout repository.
2. Detect changed components.
3. Install dependencies.
4. Run frontend lint.
5. Run frontend tests.
6. Run backend lint.
7. Run backend unit tests.
8. Run backend integration tests with test PostgreSQL.
9. Build backend Docker image.
10. Build frontend Docker image.
11. Scan images.
12. Tag images:
    - commit SHA
    - branch name
    - semantic version for releases
13. Push images to Docker Hub private repo.
14. Update Helm release with new image tags.
15. Run database migrations.
16. Deploy with Helm upgrade.
17. Run smoke tests.
18. Notify success/failure.

---

## 15.3 Branching Strategy

Recommended:

```text
main        -> production
develop     -> staging/dev
feature/*   -> feature work
hotfix/*    -> urgent fixes
```

If only one environment:

- Use `main` for production.
- Use pull requests and tests before merge.

---

## 15.4 Deployment Gates

Before production deployment:

- Unit tests pass.
- Integration tests pass.
- Docker image scan has no critical vulnerabilities.
- Database migration reviewed.
- Manual approval optional for production.

---

# 16. Monitoring and Observability

## 16.1 Metrics

Use Prometheus to collect:

### Infrastructure

- CPU usage
- Memory usage
- Disk usage
- Network traffic
- Node availability

### Kubernetes

- Pod status
- Restarts
- Deployment replicas
- CPU/memory per pod
- PVC usage

### Application

- HTTP request count
- HTTP latency
- Error rate
- Background job failures
- Report generation duration
- Login failures
- Donation creation count
- Expense approval count

### PostgreSQL

- Connections
- Query latency
- Lock waits
- Database size
- Slow queries
- Replication not applicable on single node

---

## 16.2 Grafana Dashboards

Create dashboards for:

1. System overview
2. Kubernetes overview
3. Backend API performance
4. PostgreSQL health
5. Business metrics
6. Jenkins deployment history
7. Background jobs

Business metrics dashboard:

- Total donations today/week/month
- Donations by type
- Number of active donors
- Pending custody expenses
- Custody balance
- Failed scheduled reports

---

## 16.3 Alerts

Configure Alertmanager alerts:

| Alert | Condition |
|---|---|
| AppDown | Backend unavailable |
| HighErrorRate | 5xx rate above threshold |
| HighLatency | API p95 latency too high |
| DiskAlmostFull | Disk usage over 80% |
| DatabaseDown | PostgreSQL unreachable |
| PodCrashLooping | Pod restarting repeatedly |
| BackupFailed | Backup CronJob failed |
| ReportJobFailed | Scheduled report failed |
| CertificateExpiring | TLS certificate near expiration |
| JenkinsDeployFailed | Deployment failed |

---

## 16.4 Logging

Recommended:

- Loki + Promtail
- Structured JSON application logs
- Correlation/request IDs
- Audit logs stored in database

Log retention:

- Application logs: 14-30 days
- Audit logs: 1-7 years depending on compliance need

---

# 17. Security Plan

## 17.1 Authentication

- JWT access token with short lifetime.
- Refresh token with longer lifetime.
- Store refresh token securely.
- Password hashing using strong algorithm.
- Account disable feature.
- Optional MFA for admins.

---

## 17.2 Authorization

- Role-based access control.
- Backend must enforce permissions.
- Frontend role checks are only for UI convenience and not security.

---

## 17.3 Data Protection

- HTTPS with TLS certificates.
- Encrypt backups.
- S3 bucket private with versioning.
- Sensitive secrets stored in Kubernetes Secrets or external secret store.
- Do not store plaintext passwords.
- Mask sensitive data in logs.

---

## 17.4 Infrastructure Security

- Restrict SSH to admin IP.
- Restrict Jenkins UI to admin IP/VPN.
- Do not expose PostgreSQL publicly.
- Do not expose Redis publicly.
- Use least-privilege IAM roles.
- Patch servers regularly.
- Enable unattended security updates.
- Use fail2ban optional.
- Disable root SSH login.

---

## 17.5 Jenkins Security

- Do not store secrets in repository.
- Use Jenkins credentials store.
- Restrict kubeconfig permissions.
- Jenkins should only be able to deploy to required namespace.
- Require login.
- Disable anonymous access.
- Keep plugins updated.

---

## 17.6 Application Security

- Input validation.
- SQL injection prevention through SQLAlchemy parameterization.
- Rate limiting on auth endpoints.
- CSRF consideration depending on token storage method.
- CORS restricted to allowed domains.
- Audit logging for sensitive operations.
- Soft delete instead of hard delete for financial records.
- Prevent editing approved financial records without audit trail.

---

# 18. Testing Strategy

## 18.1 Backend Testing

Types:

- Unit tests
- Service-layer tests
- API tests
- Integration tests with PostgreSQL
- Authorization tests
- Migration tests

Important test scenarios:

- Create donor.
- Search donor by phone/name/id.
- Create donation.
- Donation updates donor total.
- Donation type filtering.
- Custody assignment.
- Submit expense.
- Approve expense.
- Reject expense.
- Prevent expense over available custody.
- Report generation.
- Scheduled report execution.
- Role permissions.

---

## 18.2 Frontend Testing

Types:

- Component tests
- Page tests
- Form validation tests
- Role-based rendering tests
- API integration tests with mock server
- End-to-end tests

Important scenarios:

- Login.
- Dashboard loads.
- Add donor.
- Add donation.
- Search/filter.
- Submit custody expense.
- Approve expense.
- Generate/download report.
- Admin user management.

---

## 18.3 End-to-End Testing

Recommended tool:

- Playwright

Critical E2E flows:

1. Admin logs in.
2. Admin creates donation type.
3. Admin creates donor.
4. Admin creates donation.
5. Dashboard statistics update.
6. Admin assigns custody to user.
7. User submits expense.
8. Finance approves expense.
9. User sees updated custody balance.
10. Admin generates donation report.

---

## 18.4 Performance Testing

Use:

- k6 or Locust

Test:

- Donation search
- Donor search
- Dashboard summary
- Report generation
- Login load

---

## 18.5 Security Testing

Include:

- Dependency scanning
- Container image scanning
- OWASP checks
- Auth bypass testing
- Role-permission testing
- SQL injection testing
- XSS testing

---

# 19. Deployment Strategy

## 19.1 Environment Strategy

Recommended environments:

1. Development locally
2. Staging in k3s namespace
3. Production in k3s namespace

If infrastructure budget is limited:

- Use one cluster with two namespaces:
  - `charity-staging`
  - `charity-prod`

---

## 19.2 Release Strategy

For single EC2:

- Use rolling deployment.
- Keep at least 2 backend replicas if resources allow.
- Frontend can have 2 replicas.
- Worker can have 1 replica initially.
- PostgreSQL remains single instance.

Deployment flow:

1. Backup database.
2. Deploy migration job.
3. Deploy backend.
4. Deploy worker.
5. Deploy frontend.
6. Run smoke tests.
7. Monitor logs and metrics.

---

## 19.3 Rollback Strategy

Rollback options:

- Helm rollback to previous release.
- Use previous Docker image tag.
- Database rollback is harder.

Important rule:

Database migrations should be backward-compatible where possible.

Recommended migration approach:

- Expand/contract pattern.
- Avoid destructive changes in same release.
- Always backup before migrations.

---

## 19.4 Backup and Restore

Backup schedule:

| Backup Type | Frequency |
|---|---|
| PostgreSQL full backup | Daily |
| PostgreSQL pre-deploy backup | Before every production deploy |
| Generated reports backup | Daily or S3-native |
| Terraform state backup | Remote backend recommended |

Retention:

- Daily backups: 14-30 days
- Monthly backups: 6-12 months

Restore testing:

- Test restore monthly.
- Document restore steps.

---

# 20. Key Design Challenges and Recommendations

## 20.1 Single EC2 Is a Bottleneck

Problem:

- App, DB, monitoring, and ingress run on one machine.
- If EC2 fails, everything is down.
- Disk failure risks data loss.
- Monitoring becomes unavailable during incident.

Recommendation:

Short-term:

- Use strong backups.
- Use EBS snapshots.
- Use S3 backups.
- Use instance recovery alarm.

Long-term:

- Move PostgreSQL to RDS.
- Use multiple nodes.
- Use managed Kubernetes or EKS.
- Use external monitoring.

---

## 20.2 PostgreSQL Inside k3s Is Risky

Problem:

- Stateful workloads on single-node k3s are fragile.
- Accidental PVC deletion can be catastrophic.
- Upgrade mistakes can affect DB.

Recommendation:

- If budget allows, use RDS.
- If not, use Bitnami PostgreSQL Helm chart with persistence and daily backups.
- Never deploy DB without tested restore process.

---

## 20.3 Docker Runtime with k3s

Problem:

- k3s is designed for containerd.
- Docker runtime adds complexity.

Recommendation:

- Use Docker only in Jenkins for builds.
- Let k3s use containerd.
- If mandatory, document cri-dockerd installation and maintenance.

---

## 20.4 Dashboard Statistics Can Become Slow

Problem:

- Aggregations over donations can become slow as data grows.

Recommendation:

- Add indexes on date/type/donor.
- Use optimized SQL queries.
- Cache dashboard results for short periods.
- Consider materialized views for large data.
- Precompute daily donation summaries if dataset becomes large.

---

## 20.5 Reports Can Block API

Problem:

- Large PDF/Excel generation can slow backend.

Recommendation:

- Generate large reports asynchronously in worker.
- Store generated files.
- Notify user when ready.
- Put timeout limits on synchronous reports.

---

## 20.6 Custody Accounting Must Be Ledger-Based

Problem:

- Updating a single custody balance directly can cause errors.
- Concurrent approvals may overdraw custody.

Recommendation:

- Compute balance from assignment amount minus approved expenses.
- Use transactions and row locking during approval.
- Do not allow approved expenses to be edited without reversal/audit process.

---

## 20.7 Jenkins Has Powerful Cluster Access

Problem:

- If Jenkins is compromised, production is compromised.

Recommendation:

- Restrict Jenkins network access.
- Use namespace-limited kubeconfig.
- Use least privilege.
- Rotate credentials.
- Keep Jenkins patched.

---

# 21. Implementation Milestones

Estimated timeline: **14 weeks** for a production-ready MVP with proper infrastructure, CI/CD, monitoring, and testing.

Can be shortened to 8-10 weeks if reducing reports, monitoring, and testing scope.

---

## Phase 0: Project Setup and Final Requirements

Duration: 1 week

Tasks:

1. Confirm final feature list.
2. Confirm language/currency/date format.
3. Confirm roles and permissions.
4. Confirm report formats.
5. Confirm email provider.
6. Confirm AWS region and domain.
7. Confirm production environment constraints.
8. Create repository structure.
9. Define coding standards.
10. Define acceptance criteria.

Dependencies:

- Stakeholder decisions
- Domain access
- AWS account access

Deliverables:

- Final requirements document
- Architecture decision record
- Initial backlog
- Repository initialized

---

## Phase 1: Infrastructure Foundation

Duration: 1.5 weeks

Tasks:

1. Design AWS network.
2. Create Terraform modules.
3. Provision app EC2.
4. Provision Jenkins EC2.
5. Create security groups.
6. Create IAM roles.
7. Create S3 backup bucket.
8. Configure DNS.
9. Configure Terraform remote state if required.
10. Validate SSH access.
11. Document infrastructure.

Dependencies:

- AWS credentials
- Domain/DNS access

Deliverables:

- Terraform-managed infrastructure
- App server online
- Jenkins server online
- S3 bucket ready

---

## Phase 2: Server Configuration with Ansible

Duration: 1 week

Tasks:

1. Create Ansible inventory.
2. Create common server hardening role.
3. Configure app server.
4. Install k3s.
5. Install Helm and kubectl.
6. Install Docker if required.
7. Configure Jenkins server.
8. Install Jenkins.
9. Install Docker on Jenkins.
10. Install Helm/kubectl on Jenkins.
11. Configure Jenkins credentials.
12. Validate Jenkins can reach k3s.

Dependencies:

- Phase 1 complete

Deliverables:

- Configured app server
- Configured Jenkins server
- Running k3s cluster
- Jenkins ready for pipelines

---

## Phase 3: Kubernetes Platform Setup

Duration: 1 week

Tasks:

1. Create Kubernetes namespaces.
2. Install ingress-nginx.
3. Install cert-manager.
4. Configure TLS issuer.
5. Install PostgreSQL Helm release.
6. Install Redis Helm release.
7. Install Prometheus.
8. Install Grafana.
9. Configure Grafana admin access.
10. Configure persistent volumes.
11. Validate ingress routing.
12. Validate TLS certificate generation.

Dependencies:

- Phase 2 complete
- DNS configured

Deliverables:

- k3s platform ready
- PostgreSQL and Redis available
- Monitoring stack installed
- HTTPS ingress ready

---

## Phase 4: Backend Foundation

Duration: 1.5 weeks

Tasks:

1. Create backend project structure.
2. Configure FastAPI application foundation.
3. Configure SQLAlchemy.
4. Configure Alembic migrations.
5. Define base models.
6. Implement health endpoint.
7. Implement configuration management.
8. Implement structured logging.
9. Implement error handling.
10. Implement authentication foundation.
11. Implement RBAC foundation.
12. Create initial database migration.
13. Create Dockerfile.
14. Add backend test setup.

Dependencies:

- Database schema finalized
- PostgreSQL available locally or in dev

Deliverables:

- Backend skeleton
- Database migration system
- Auth/RBAC foundation
- Health check
- Backend container buildable

---

## Phase 5: Frontend Foundation

Duration: 1 week

Tasks:

1. Create frontend project structure.
2. Configure routing.
3. Configure UI framework.
4. Create layout/sidebar.
5. Create login page.
6. Create role-based navigation.
7. Configure API client.
8. Configure authentication state.
9. Create protected route handling.
10. Create reusable table component.
11. Create reusable form components.
12. Create Dockerfile.

Dependencies:

- Backend auth API available or mocked

Deliverables:

- Frontend skeleton
- Login flow
- Dashboard layout
- Reusable UI components

---

## Phase 6: Users, Auth, and Profile

Duration: 1 week

Tasks:

1. Implement login.
2. Implement refresh tokens.
3. Implement logout.
4. Implement password change.
5. Implement current profile endpoint.
6. Implement profile update.
7. Implement users CRUD.
8. Implement role assignment.
9. Implement user disable.
10. Implement frontend user management pages.
11. Implement frontend profile page.
12. Add audit logging for user changes.
13. Add tests.

Dependencies:

- Backend and frontend foundations complete

Deliverables:

- Secure login
- Role-based admin user management
- Profile management

---

## Phase 7: Donors Module

Duration: 1 week

Tasks:

1. Create donor database migrations.
2. Implement donor create API.
3. Implement donor update API.
4. Implement donor search/list API.
5. Implement donor detail API.
6. Implement donor notes API.
7. Implement phone/address management.
8. Add donor indexes.
9. Create donor frontend list page.
10. Create donor search/filter UI.
11. Create donor create/edit form.
12. Create donor detail page.
13. Add tests.

Dependencies:

- Auth/RBAC complete

Deliverables:

- Donor management module

---

## Phase 8: Donation Types and Donations

Duration: 1.5 weeks

Tasks:

1. Create donation type migration.
2. Create donation migration.
3. Implement donation type APIs.
4. Implement donation APIs.
5. Implement donation search/filter.
6. Implement donation notes.
7. Implement donation status handling.
8. Implement donor total/last donation logic.
9. Add donation indexes.
10. Create donation type frontend page.
11. Create donations list page.
12. Create donation creation form.
13. Create donation detail page.
14. Add tests.

Dependencies:

- Donors module complete

Deliverables:

- Donation type management
- Donation management

---

## Phase 9: Custody and Approval Workflow

Duration: 1.5 weeks

Tasks:

1. Create custody assignment migration.
2. Create custody expense migration.
3. Create approval migration.
4. Implement custody assignment API.
5. Implement custody search/filter.
6. Implement user custody summary.
7. Implement expense submission.
8. Implement approval/rejection APIs.
9. Implement balance calculation.
10. Implement transaction safety for approvals.
11. Implement profile custody UI.
12. Implement custody admin UI.
13. Implement approvals UI.
14. Add audit logs.
15. Add tests for overdraw prevention and permissions.

Dependencies:

- Users/RBAC complete

Deliverables:

- Custody assignment
- Expense submission
- Approval workflow

---

## Phase 10: Dashboard Statistics

Duration: 1 week

Tasks:

1. Define dashboard query requirements.
2. Implement summary APIs.
3. Implement donations by type API.
4. Implement recent active donors API.
5. Implement custody summary API.
6. Optimize queries.
7. Add indexes if needed.
8. Create frontend dashboard cards.
9. Create dashboard charts.
10. Add period selector.
11. Add loading/error states.
12. Add tests.

Dependencies:

- Donations and custody modules complete

Deliverables:

- Home dashboard with statistics

---

## Phase 11: Reports and Scheduled Reports

Duration: 2 weeks

Tasks:

1. Define report templates.
2. Implement donation report data API.
3. Implement donor report data API.
4. Implement custody report data API.
5. Implement chart-ready report responses.
6. Implement CSV generation.
7. Implement PDF generation.
8. Implement generated report records.
9. Implement report download.
10. Implement scheduled report CRUD.
11. Configure background worker.
12. Configure email provider.
13. Implement weekly/monthly/yearly schedules.
14. Implement report email sending.
15. Create reports frontend page.
16. Create scheduled reports frontend page.
17. Add tests.

Dependencies:

- Donations, donors, custody complete
- Redis/worker available
- Email provider confirmed

Deliverables:

- Manual reports
- Downloadable reports
- Scheduled automatic reports

---

## Phase 12: CI/CD Pipeline

Duration: 1 week

Tasks:

1. Create Jenkins pipeline definition.
2. Add backend lint/test stages.
3. Add frontend lint/test stages.
4. Add Docker build stages.
5. Add Docker Hub push.
6. Add image tag strategy.
7. Add Helm deployment stage.
8. Add migration job stage.
9. Add smoke tests.
10. Add rollback documentation.
11. Add notifications.
12. Test full pipeline.

Dependencies:

- App containers exist
- Helm chart exists
- Jenkins configured

Deliverables:

- Automated build/test/deploy pipeline

---

## Phase 13: Monitoring, Logging, and Alerts

Duration: 1 week

Tasks:

1. Configure backend metrics endpoint.
2. Configure Prometheus scraping.
3. Create Grafana dashboards.
4. Configure PostgreSQL exporter.
5. Configure Redis exporter.
6. Configure Kubernetes dashboards.
7. Configure Loki/Promtail.
8. Configure Alertmanager.
9. Add backup failure alert.
10. Add application error alerts.
11. Add disk usage alert.
12. Validate alert delivery.

Dependencies:

- App deployed
- Monitoring stack installed

Deliverables:

- Production observability stack
- Alerts configured

---

## Phase 14: Security Hardening and Final Testing

Duration: 1 week

Tasks:

1. Review role permissions.
2. Run security scan.
3. Run dependency scan.
4. Run image scan.
5. Validate secrets are not in Git.
6. Validate HTTPS.
7. Validate CORS.
8. Validate auth flows.
9. Validate audit logs.
10. Run E2E tests.
11. Run performance tests.
12. Test backup and restore.
13. Test deployment rollback.
14. Fix critical bugs.

Dependencies:

- Full system complete

Deliverables:

- Security-reviewed system
- Tested backup/restore
- Production readiness approval

---

## Phase 15: Production Launch

Duration: 0.5 week

Tasks:

1. Freeze release branch.
2. Take database backup.
3. Deploy final production release.
4. Run migrations.
5. Run smoke tests.
6. Create initial admin user.
7. Configure scheduled backups.
8. Configure scheduled reports.
9. Monitor system for 24-48 hours.
10. Handover documentation.

Dependencies:

- Phase 14 complete

Deliverables:

- Production system live
- Admin access ready
- Monitoring active

---

# 22. Task Dependency Map

```text
Phase 0 Requirements
        |
        v
Phase 1 Terraform Infrastructure
        |
        v
Phase 2 Ansible Server Config
        |
        v
Phase 3 Kubernetes Platform
        |
        +--------------------+
        |                    |
        v                    v
Phase 4 Backend          Phase 5 Frontend
        |                    |
        +---------+----------+
                  |
                  v
Phase 6 Auth/Profile/Users
                  |
        +---------+----------+
        |                    |
        v                    v
Phase 7 Donors       Phase 9 Custody
        |
        v
Phase 8 Donations
        |
        v
Phase 10 Dashboard
        |
        v
Phase 11 Reports
        |
        v
Phase 12 CI/CD
        |
        v
Phase 13 Monitoring
        |
        v
Phase 14 Security/Testing
        |
        v
Phase 15 Production Launch
```

Some phases can overlap:

- Frontend foundation can start while backend foundation is being built.
- Infrastructure can start while database design is finalized.
- Monitoring can start after k3s is ready.
- CI/CD can start once first containerized services exist.

---

# 23. Estimated Timeline Summary

| Phase | Duration |
|---|---:|
| Phase 0: Requirements | 1 week |
| Phase 1: Terraform Infrastructure | 1.5 weeks |
| Phase 2: Ansible Configuration | 1 week |
| Phase 3: Kubernetes Platform | 1 week |
| Phase 4: Backend Foundation | 1.5 weeks |
| Phase 5: Frontend Foundation | 1 week |
| Phase 6: Users/Auth/Profile | 1 week |
| Phase 7: Donors | 1 week |
| Phase 8: Donations | 1.5 weeks |
| Phase 9: Custody/Approval | 1.5 weeks |
| Phase 10: Dashboard | 1 week |
| Phase 11: Reports | 2 weeks |
| Phase 12: CI/CD | 1 week |
| Phase 13: Monitoring | 1 week |
| Phase 14: Security/Testing | 1 week |
| Phase 15: Launch | 0.5 week |

Total estimated duration:

```text
14-16 weeks
```

With parallel work:

```text
10-12 weeks possible
```

---

# 24. Main Risks

## Risk 1: Single EC2 Failure

Impact:

- Full system outage.
- Possible data loss if backups fail.

Mitigation:

- Daily backups to S3.
- EBS snapshots.
- Restore testing.
- Future migration to RDS/multi-node.

---

## Risk 2: Database Corruption or Data Loss

Impact:

- Severe financial/accounting issue.

Mitigation:

- Backups.
- Audit logs.
- Soft deletes.
- Migration testing.
- Restricted DB access.

---

## Risk 3: Incorrect Custody Balance

Impact:

- Financial discrepancy.

Mitigation:

- Ledger-based design.
- Transactional approval flow.
- Prevent direct balance mutation.
- Audit all financial actions.

---

## Risk 4: Slow Dashboard/Reports

Impact:

- Bad user experience.

Mitigation:

- Indexes.
- Async report generation.
- Caching.
- Summary tables/materialized views later.

---

## Risk 5: Jenkins Compromise

Impact:

- Production deployment compromise.

Mitigation:

- Restrict Jenkins access.
- Use limited kubeconfig.
- Keep Jenkins patched.
- Rotate credentials.

---

## Risk 6: Secrets Exposure

Impact:

- Database or system compromise.

Mitigation:

- Jenkins credentials store.
- Kubernetes Secrets.
- No secrets in Git.
- Secret scanning.

---

## Risk 7: Scope Creep

Impact:

- Delayed delivery.

Mitigation:

- Define MVP clearly.
- Prioritize critical modules.
- Defer public online donations/payment integration unless required.

---

# 25. MVP Scope Recommendation

To launch faster, define MVP as:

1. Landing page
2. Login/RBAC
3. Users
4. Donors
5. Donation types
6. Donations
7. Custody assignment
8. Expense submission
9. Approval workflow
10. Basic dashboard
11. Basic donation/donor reports
12. CI/CD
13. Backups
14. Monitoring basics

Defer to v2:

- Advanced scheduled reports
- Excel exports
- MFA
- Complex report designer
- Public donation/payment integration
- Multi-branch organization support
- Mobile app

---

# 26. Final Recommended Deployment Architecture

```text
AWS Account
|
+-- EC2: app-server
|     |
|     +-- k3s
|          |
|          +-- ingress-nginx
|          +-- cert-manager
|          +-- frontend
|          +-- backend-api
|          +-- worker
|          +-- postgresql
|          +-- redis
|          +-- prometheus
|          +-- grafana
|          +-- loki/promtail
|
+-- EC2: jenkins-server
|     |
|     +-- Jenkins
|     +-- Docker build engine
|     +-- Helm
|     +-- kubectl
|
+-- S3
|     |
|     +-- database backups
|     +-- generated reports
|
+-- Docker Hub Private Repo
      |
      +-- frontend image
      +-- backend image
      +-- worker image
```

---

# 27. Final Notes

The project is very achievable with your requested stack. The most important architectural decisions are:

1. Use **ledger-style custody accounting**.
2. Use **asynchronous background jobs** for reports and emails.
3. Do not expose database, Redis, or Jenkins publicly.
4. Use **S3 backups** from day one.
5. Prefer **k3s containerd runtime**, even if Docker is used for image building.
6. Treat the single EC2 design as an MVP deployment, not long-term high-availability production architecture.
7. Build strong audit logging because this system handles financial records.