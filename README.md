# Mini CRM

A professional Mini CRM built with **Python Flask**, **SQLAlchemy**, **Flask-Login**, **SQLite**, and **Bootstrap 5**.

Manage contacts, companies, and deals with a clean MVC architecture and Flask Blueprints.

## Features

- **Authentication module**
  - Login / Logout with Flask-Login session management
  - Admin and Employee account roles
  - Password hashing (Werkzeug)
  - Remember me (persistent sessions)
  - Protected routes (`@login_required`, `@admin_required`)
  - Bootstrap login & register pages with flash messages and form validation
  - Redirect to dashboard after login
- **Professional CRM dashboard**
  - KPI cards: Total Leads, Today's Leads, Customers, Follow-ups Today, Won/Lost Deals
  - Sidebar + navbar with profile dropdown
  - Responsive Bootstrap layout
  - Chart.js charts (lead trend, outcomes, pipeline, revenue)
  - Recent activities feed (demo data)
- **Lead Management**
  - Fields: name, company, email, phone, country, industry, source, status, assigned employee, notes
  - Add / Edit / Delete with confirmation modal
  - Search, filter, pagination
  - Form validation + activity log on every action
  - Responsive Bootstrap table
  - Convert Lead → Customer
- **Customer Management**
  - Address, GST, Website, Industry, Primary Contact, Notes
  - Customer list / details with CRUD
  - Search, pagination, responsive UI
- **Follow-up Management**
  - Schedule Call / Meeting / WhatsApp / Email
  - Reminder date & time, status, remarks
  - Today's / Upcoming / Missed buckets
  - Bootstrap month calendar view
- **Task Management**
  - Create tasks, assign employees, priority & status
  - Due date / completed date
  - Search, filters, task dashboard, color badges
- **Reports**
  - Chart.js: Monthly Leads, Lead Sources, Won vs Lost, Employee Performance, Customer Growth
  - Export each report to CSV
- **Settings**
  - Company name, logo upload, timezone, currency
  - SMTP settings, theme (light/dark/ocean)
  - Database backup & restore
  - Profile update & password change
- **Admin Panel** (Admin only)
  - Bootstrap admin dashboard (user / role KPIs)
  - Manage users: create, edit, activate / deactivate, delete
  - Roles: Admin, Manager, Employee
  - Per-user permissions with role defaults
  - Reset password
  - Login history (success / failed attempts)
- **Activity Log**
  - Tracks Login, Logout, Lead Created/Updated/Deleted, Customer Created, Task Created/Completed
  - Stores Date, Time, IP Address, and User
  - Bootstrap table with search, filters, and pagination (`/activities`)
- **CSV Import / Export**
  - Import & export Leads and Customers
  - Full CSV validation before import (headers, required fields, email, enums)
  - Bootstrap error table when validation fails — nothing imported on error
  - Sample CSV downloads at `/csv`
- **SMTP Email**
  - Send email to a lead from a Bootstrap compose window
  - Email templates with placeholders (`{{name}}`, `{{company}}`, etc.)
  - Track sent/failed emails and store full email history
  - Uses SMTP settings from Settings → SMTP
- **WhatsApp Integration**
  - Store WhatsApp numbers on Leads and Customers
  - Open WhatsApp chat (`wa.me`) with predefined messages
  - Message history with status tracking
  - Provider scaffold ready for WhatsApp Business API
- Full CRUD for **Contacts**, **Companies**, and **Deals**
- Search and filter on list views
- Ownership-scoped data (users only see their own records)
- CSRF-protected forms (Flask-WTF)
- SQLite database created automatically on startup
- Environment-based configuration via `.env`

## Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Language     | Python 3.12                         |
| Framework    | Flask                               |
| ORM          | SQLAlchemy (Flask-SQLAlchemy)       |
| Auth         | Flask-Login                         |
| Forms        | Flask-WTF / WTForms                 |
| Database     | SQLite                              |
| Frontend     | Bootstrap 5, HTML, CSS, JavaScript  |

## Project Structure

```
.
├── app.py                 # Application entry point
├── config.py              # Configuration (.env support)
├── requirements.txt
├── .env.example
├── README.md
├── wsgi.py                # Production WSGI entry (gunicorn)
├── Procfile               # Process definition for PaaS deploys
├── app.py                 # Local development entry
└── app/
    ├── __init__.py        # App factory
    ├── seed.py            # Startup seed helpers
    ├── extensions.py      # SQLAlchemy, LoginManager, CSRF
    ├── decorators.py      # Authn / authz helpers
    ├── forms.py           # WTForms
    ├── models.py          # SQLAlchemy models
    ├── utils/             # Shared pagination, redirects, DB helpers
    ├── blueprints/        # Route controllers
    ├── services/          # Domain services (email, whatsapp, csv, …)
    ├── templates/
    └── static/
```

## Setup Instructions

### 1. Prerequisites

- Python 3.12+
- `pip` and `venv`

### 2. Clone and create a virtual environment

```bash
cd mini-crm   # or your project directory
python3.12 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` for local development:

```env
FLASK_APP=wsgi:app
FLASK_ENV=development
SECRET_KEY=change-this-to-a-long-random-secret
DATABASE_URL=sqlite:///instance/crm.db
SEED_DEMO_USERS=true
ALLOW_PUBLIC_REGISTRATION=true
```

### 5. Run locally

```bash
python app.py
# or
flask --app wsgi:app run
```

The app starts at [http://127.0.0.1:5000](http://127.0.0.1:5000).  
SQLite tables are created automatically on startup.

### 6. Sign in

Default **Admin** (development only):

| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `admin123` |

Override via `ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

## Deployment

Use the WSGI entrypoint with **gunicorn** (included in `requirements.txt`):

```bash
export FLASK_ENV=production
export SECRET_KEY="$(openssl rand -hex 32)"
export ADMIN_PASSWORD="replace-with-a-strong-password"
export ALLOW_PUBLIC_REGISTRATION=false
export SEED_DEMO_USERS=false
gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 2
```

Or on platforms that read a Procfile:

```bash
# Procfile
web: gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2
```

Production config **requires** a non-default `SECRET_KEY` and `ADMIN_PASSWORD`.

Health checks:

| Endpoint  | Purpose                |
|-----------|------------------------|
| `/health` | Liveness (always 200)  |
| `/ready`  | DB readiness           |

Notes for production:

- Put TLS termination and static caching on a reverse proxy (nginx / cloud load balancer)
- Prefer Postgres (`DATABASE_URL=postgresql+psycopg://...`) for multi-worker deploys
- Keep `.env` out of source control
- Disable public registration unless intentionally needed

## Authentication

| Route       | Description                                      |
|-------------|--------------------------------------------------|
| `/login`    | Bootstrap login form (Remember me supported)     |
| `/register` | Create an Employee account (optional / flag)     |
| `/logout`   | End session (CSRF-protected POST)                |
| `/`         | Dashboard — requires login                       |

- Passwords are hashed with Werkzeug
- Sessions are managed by Flask-Login
- Route guards live in `app/decorators.py` (`admin_required`, `permission_required`)

## Usage Overview

| Module     | Path          | Description                                      |
|------------|---------------|--------------------------------------------------|
| Dashboard  | `/`           | Stats, charts, recent activities                 |
| Leads      | `/leads`      | Lead management with search, filters, activity   |
| Customers  | `/customers`  | Customers + convert from leads                   |
| Follow-ups | `/followups`  | Schedule reminders + calendar                    |
| Tasks      | `/tasks`      | Task list + `/tasks/dashboard`                   |
| Reports    | `/reports`    | Charts + CSV export                              |
| Settings   | `/settings`   | Company, SMTP, theme, backup, profile            |
| Admin      | `/admin`      | Users, roles, permissions, login history         |
| Activities | `/activities` | Cross-module activity log                        |
| CSV        | `/csv`        | Lead/customer import & export                    |
| Emails     | `/emails`     | SMTP compose, templates, history                 |
| WhatsApp   | `/whatsapp`   | Click-to-chat compose, templates, history        |
| Contacts   | `/contacts`   | People linked to companies                       |
| Companies  | `/companies`  | Organizations you work with                       |
| Deals      | `/deals`      | Sales opportunities with stages & values         |

Deal stages: Prospecting → Qualification → Proposal → Negotiation → Closed Won / Closed Lost.

## Configuration

Configuration is loaded from environment variables in `config.py` via `python-dotenv`:

| Variable                    | Description                         | Default                 |
|-----------------------------|-------------------------------------|-------------------------|
| `SECRET_KEY`                | Flask session / CSRF secret         | dev placeholder         |
| `DATABASE_URL`              | SQLAlchemy database URI             | `sqlite:///instance/crm.db` |
| `FLASK_ENV`                 | `development` or `production`       | `development`           |
| `ADMIN_USERNAME`            | Seeded admin username               | `admin`                 |
| `ADMIN_EMAIL`               | Seeded admin email                  | `admin@minicrm.local`   |
| `ADMIN_PASSWORD`            | Seeded admin password               | `admin123`              |
| `SEED_DEMO_USERS`           | Seed sample employee account        | `true` (dev)            |
| `ALLOW_PUBLIC_REGISTRATION` | Enable `/register`                  | `true` (dev) / `false` (prod) |
| `MAIL_SUPPRESS_SEND`        | Skip SMTP delivery (store history)  | `false`                 |

## Development Notes

- Architecture follows **MVC**: models in `app/models.py`, controllers as blueprints, views as Jinja templates.
- Shared helpers live in `app/utils/`; domain logic in `app/services/`.
- Extensions are centralized in `app/extensions.py`.
- Use `create_app("development")` / `create_app("production")` for tests or alternate configs.

## License

MIT
