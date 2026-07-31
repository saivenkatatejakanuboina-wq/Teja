"""Development entry point for the Mini CRM Flask application.

For production, use ``wsgi.py`` with gunicorn (see Procfile / README).
"""

import os

from app import create_app

# Local `python app.py` defaults to development; never force debug in production.
_env = os.getenv("FLASK_ENV", "development")
app = create_app(_env)


if __name__ == "__main__":
    debug = _env != "production" and app.config.get("DEBUG", False)
    port = int(os.getenv("PORT", "5000"))
    # Bind 127.0.0.1 by default; set HOST=0.0.0.0 only when intentionally exposing.
    host = os.getenv("HOST", "127.0.0.1")
    app.run(debug=debug, host=host, port=port)
