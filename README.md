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
└── app/
    ├── __init__.py        # App factory (creates DB + seeds Admin)
    ├── extensions.py      # SQLAlchemy, LoginManager, CSRF
    ├── decorators.py      # Protected route helpers
    ├── forms.py           # WTForms (incl. Login / Register)
    ├── models.py          # Model layer (User, Company, Contact, Deal)
    ├── blueprints/        # Controllers (MVC)
    │   ├── auth.py        # Auth blueprint
    │   ├── dashboard.py
    │   ├── leads.py       # Lead Management
    │   ├── customers.py   # Customer Management
    │   ├── followups.py   # Follow-up Management
    │   ├── tasks.py       # Task Management
    │   ├── reports.py     # Reports + CSV export
    │   ├── settings.py    # Settings module
    │   ├── admin.py       # Admin Panel
    │   ├── activities.py  # Activity Log
    │   ├── csv_io.py      # CSV Import / Export
    │   ├── companies.py
    │   ├── contacts.py
    │   └── deals.py
    ├── services/
    │   ├── activity.py    # Activity log helper
    │   ├── admin_service.py
    │   ├── csv_io.py      # CSV validate / import / export
    │   ├── reports.py     # Report aggregations
    │   └── settings_service.py
    ├── templates/         # Views (MVC)
    │   ├── admin/         # Admin dashboard, users, roles, history
    │   ├── activities/    # Activity Log table
    │   ├── csv/           # CSV Import / Export UI
    │   └── auth/
    │       ├── login.html
    │       └── register.html
    └── static/
        ├── css/style.css
        └── js/app.js
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

Edit `.env` as needed:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=change-this-to-a-long-random-secret
DATABASE_URL=sqlite:///crm.db
```

### 5. Run the application

```bash
python app.py
```

Or with the Flask CLI:

```bash
flask run
```

The app starts at [http://127.0.0.1:5000](http://127.0.0.1:5000).

The SQLite database (`crm.db`) is created automatically on first launch — no migration step required.

### 6. Sign in

A default **Admin** account is created automatically:

| Field    | Value               |
|----------|---------------------|
| Username | `admin`             |
| Password | `admin123`          |
| Role     | Admin               |

1. Open [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)
2. Sign in as Admin, **or** register a new **Employee** account
3. After login you are redirected to the **Dashboard** (`/`)

Override the default admin via `.env` (`ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`).

## Authentication

| Route       | Description                                      |
|-------------|--------------------------------------------------|
| `/login`    | Bootstrap login form (Remember me supported)     |
| `/register` | Create an Employee account                       |
| `/logout`   | End session (protected)                          |
| `/`         | Dashboard — requires login                       |

- Passwords are hashed with Werkzeug (`generate_password_hash` / `check_password_hash`)
- Sessions are managed by Flask-Login (`login_user` / `logout_user` / `user_loader`)
- CRM routes use `@login_required`; admin-only helpers live in `app/decorators.py`

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
| Contacts   | `/contacts`   | People linked to companies                       |
| Companies  | `/companies`  | Organizations you work with                       |
| Deals      | `/deals`      | Sales opportunities with stages & values         |

Deal stages: Prospecting → Qualification → Proposal → Negotiation → Closed Won / Closed Lost.

## Configuration

Configuration is loaded from environment variables in `config.py` via `python-dotenv`:

| Variable       | Description                          | Default              |
|----------------|--------------------------------------|----------------------|
| `SECRET_KEY`      | Flask session / CSRF secret     | `dev-secret-key-...`     |
| `DATABASE_URL`    | SQLAlchemy database URI         | `sqlite:///crm.db`       |
| `FLASK_ENV`       | `development` or `production`   | `development`            |
| `ADMIN_USERNAME`  | Seeded admin username           | `admin`                  |
| `ADMIN_EMAIL`     | Seeded admin email              | `admin@minicrm.local`    |
| `ADMIN_PASSWORD`  | Seeded admin password           | `admin123`               |

## Development Notes

- Architecture follows **MVC**: models in `app/models`, controllers as blueprints, views as Jinja templates.
- Extensions are centralized in `app/extensions.py`.
- Use `create_app()` for testing or alternative configs.

## License

MIT
