# LawyerBrain — Corporate-Law Legal Intelligence Platform

LawyerBrain is a client-file intelligence platform built for Indian corporate law firms. A firm creates clients, manages matters under them, retains vault documents, tracks hearings and cause lists, assigns tasks, publishes client updates, and conducts statutory and case-law research.

---

## Run it on your Mac

Follow these exact steps from a fresh terminal to run the platform locally on your Mac with the realistic demo dataset.

### Prerequisites
- macOS with Docker Desktop installed and running
- Python 3.13 and `uv`
- Node.js (v20+) and `pnpm`

---

### Step 1: Start Postgres and MinIO

From the repository root:

```bash
docker compose up -d postgres minio
```

> **Note on ports:** Docker Compose maps PostgreSQL container port `5432` to host port `5433` (`${POSTGRES_HOST_PORT:-5433}:5432`) to avoid conflicts with any local PostgreSQL instance. MinIO runs on ports `9000` (S3 API) and `9001` (web console).

---

### Step 2: Run Database Migrations

Run database migrations against the `owner` connection role:

```bash
cd backend
POSTGRES_PORT=5433 DJANGO_SETTINGS_MODULE=core.settings.local uv run python manage.py migrate --database=owner
```

---

### Step 3: Seed Demo Data

Run the idempotent `seed_demo` command to provision the "Demo Law Chambers" firm, demo accounts, and synthetic cases:

```bash
POSTGRES_PORT=5433 DJANGO_SETTINGS_MODULE=core.settings.local uv run python manage.py seed_demo
```

This sets up:
- Firm: **Demo Law Chambers**
- 20 realistic matters across 6 clients imported via the real import pipeline
- Hearing today and tomorrow
- Open task assigned to the associate
- Published client status update
- Three test accounts with different permission levels:
  - `admin@demo.law` (Firm **ADMIN**) — Can manage firm users and import cases
  - `partner@demo.law` (Firm **PARTNER**) — Matter LEAD on demo matters; can publish updates and manage share links
  - `associate@demo.law` (Firm **ASSOCIATE**) — Matter MEMBER; has assigned tasks

---

### Step 4: Start the Backend Server

Start the Django Ninja API server:

```bash
POSTGRES_PORT=5433 DJANGO_SETTINGS_MODULE=core.settings.local uv run python manage.py runserver 8000
```

The API server runs on `http://127.0.0.1:8000`.

---

### Step 5: Start the Frontend App

In a **second terminal window**, start the Vite dev server:

```bash
cd frontend
pnpm dev
```

---

### Step 6: Open the App and Sign In

Open your browser to:

👉 **http://localhost:5173**

On the Sign-In screen:
1. Click any of the quick-login buttons (`admin@demo.law`, `partner@demo.law`, or `associate@demo.law`), or type the email directly and click **Sign in**.
2. Click through the platform:
   - **Today**: Shows hearings scheduled for today and tomorrow, plus the associate's open tasks.
   - **Clients**: Lists corporate clients and their respective matters.
   - **Matters**: View matter details, documents, and hearings.
   - **Tasks**: Inspect open tasks, due dates, and assignments.
   - **Client Updates**: View and publish client status reports.
   - **Share Link**: Generate, extend, or revoke client-facing read-only status links.
   - **Import Cases** (Admin only): Upload Excel/CSV files, map headers, preview rows, apply duplicate/client overrides, and commit imports.
3. Click **Sign Out** in the navigation bar to return to the sign-in screen and switch users.
