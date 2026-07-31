"""Pagination helpers to keep list views consistent."""

from __future__ import annotations

from flask import request
from flask_sqlalchemy.pagination import Pagination


def page_arg(default: int = 1) -> int:
    """Read a positive page number from the query string."""
    page = request.args.get("page", default, type=int) or default
    return page if page > 0 else default


def paginate(query, *, per_page: int = 10, page: int | None = None) -> Pagination:
    """Paginate a SQLAlchemy query with shared defaults."""
    from app.extensions import db

    return db.paginate(
        query,
        page=page_arg() if page is None else page,
        per_page=per_page,
        error_out=False,
    )
