# Mini CRM

A professional Mini CRM built with **Python Flask**, **SQLAlchemy**, **Flask-Login**, **SQLite**, and **Bootstrap 5**.

Manage contacts, companies, and deals with a clean MVC architecture and Flask Blueprints.

## Features

- User registration, login, and session management (Flask-Login)
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
    ├── __init__.py        # App factory (creates DB automatically)
    ├── extensions.py      # SQLAlchemy, LoginManager, CSRF
    ├── forms.py           # WTForms (view helpers)
    ├── models/            # Model layer (MVC)
    │   ├── user.py
    │   ├── company.py
    │   ├── contact.py
    │   └── deal.py
    ├── blueprints/        # Controllers (MVC)
    │   ├── auth.py
    │   ├── dashboard.py
    │   ├── companies.py
    │   ├── contacts.py
    │   └── deals.py
    ├── templates/         # Views (MVC)
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

### 6. Create your account

1. Open the app in your browser
2. Click **Create one** to register
3. Sign in and start adding companies, contacts, and deals

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
| `SECRET_KEY`   | Flask session / CSRF secret          | `dev-secret-key-...` |
| `DATABASE_URL` | SQLAlchemy database URI              | `sqlite:///crm.db`   |
| `FLASK_ENV`    | `development` or `production`        | `development`        |

## Development Notes

- Architecture follows **MVC**: models in `app/models`, controllers as blueprints, views as Jinja templates.
- Extensions are centralized in `app/extensions.py`.
- Use `create_app()` for testing or alternative configs.

## License

MIT
