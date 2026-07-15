# Baytak Foundation Management

A local MVP for charity operations: donors, donation funds and receipts, user roles, custody accounting, expense approval, dashboard metrics, audit records, and CSV reports.

## Run locally

1. Optionally copy `.env.example` to `.env` and replace the local passwords/secrets.
2. Run:

   ```powershell
   docker compose up --build
   ```

3. Open:
   - App: http://localhost:8080
   - API docs: http://localhost:8000/docs
   - API health: http://localhost:8000/health

The initial local administrator is configured through `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD`. With no `.env` file, use:

```text
admin@charity.local
ChangeMe123!
```

Change this password after the first sign-in.

## Branding and logo

The supplied Baytak logo is included at `frontend/public/baytak-logo.png`. App text, sidebar tab labels, and the theme palette are configured in the root `.env` file; use the complete list in `.env.example`.

After changing any `VITE_*` value, rebuild the frontend because Vite embeds these public values into its production build:

```powershell
docker compose up -d --build frontend
```

`VITE_APP_LOGO_PATH` defaults to `/baytak-logo.png`. To use another logo, place it in `frontend/public`, set this value to its public path (for example, `/my-logo.png`), then rebuild the frontend.

## Languages

The interface includes an English/العربية language switcher on the public, sign-in, and application pages. The chosen language is saved in the browser. Set `VITE_DEFAULT_LOCALE=ar` in `.env` to start new browsers in Arabic; users can still switch languages at any time.

## Seed demonstration data

After the stack is running, populate the local database with users, donation types, donors, donations, custody assignments, pending/approved/rejected expenses, and a scheduled-report definition:

```powershell
docker compose exec backend python seed.py
```

The command is idempotent: running it again does not duplicate data. All seeded users use `ChangeMe123!`; sign in as `finance@charity.local`, `sami@charity.local`, `lina@charity.local`, or `viewer@charity.local` to exercise each role.

## API tests

The backend includes isolated API tests for every application endpoint, role-protected workflow, report download, password-reset token, and outgoing email structure. The suite uses an in-memory SQLite database and mocked SMTP delivery; it does not require Docker or a real email account.

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Manual validation sequence

1. Sign in as the administrator.
2. Create a donation type, donor, and donation; confirm dashboard totals update.
3. Create a staff user and assign custody to that account.
4. Sign in as the staff user, submit an expense, then approve/reject it as finance or admin.
5. Generate a donor, donation, or custody CSV from Reports after choosing a start and end date.
6. Create a Scheduled Report, configure recipient emails, then use **Run now** to verify SMTP delivery.

## Scheduled report email

Configure the SMTP settings in your uncommitted `.env` file, then restart the backend:

```text
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=reports@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=reports@example.com
SMTP_STARTTLS=true
```

Scheduled reports create a CSV attachment and send it to the configured recipients. The local backend checks for due schedules every minute. For local testing, use the **Run now** action on the Scheduled Reports page.

## Password reset email

The sign-in screen includes **Forgot password?**. For a user to receive its reset link, configure SMTP and set the public address used by the recipient's browser:

```text
FRONTEND_APP_URL=http://localhost:8080
PASSWORD_RESET_MINUTES=30
```

For a deployed system, `FRONTEND_APP_URL` must be the actual HTTPS application URL, not `localhost`. Reset links expire, are single-use, and revoke the user's active sessions after a successful password reset.

## Scope

This repository stops at the application and local Docker Compose layer. Terraform, Ansible, Kubernetes/Helm, Jenkins, monitoring, and cloud storage are intentionally not included.

The scheduler runs inside the single local backend process. Move it to a dedicated worker before deploying multiple backend replicas. Local reports are CSV files stored in the Compose `report_data` volume.
