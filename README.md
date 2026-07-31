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
- Dashboard with pipeline stats and recent activity
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
    │   ├── companies.py
    │   ├── contacts.py
    │   └── deals.py
    ├── templates/         # Views (MVC)
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
| Dashboard  | `/`           | Stats, recent deals & contacts, pipeline stages  |
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
