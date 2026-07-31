"""WSGI entrypoint for production servers (gunicorn / uwsgi).

Usage:
    gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 2
"""

import os

from app import create_app

# Prefer explicit FLASK_ENV / APP_ENV; default to production for this module.
_env = os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "production"
app = create_app(_env)
