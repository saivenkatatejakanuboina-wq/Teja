"""Shared SelectField choice builders for CRM forms."""

from __future__ import annotations

from app.models import Customer, Lead, User


def active_employees() -> list[User]:
    """Active users ordered for filter dropdowns and assignment lists."""
    return (
        User.query.filter_by(is_active=True)
        .order_by(User.full_name.asc())
        .all()
    )


def employee_choices(*, include_unassigned: bool = True) -> list[tuple[int, str]]:
    """Active users for assignment dropdowns."""
    choices = [
        (u.id, f"{u.full_name} ({u.role_label})")
        for u in active_employees()
    ]
    if include_unassigned:
        return [(0, "— Unassigned —")] + choices
    return choices


def lead_choices(*, include_blank: bool = True) -> list[tuple[int, str]]:
    leads = Lead.query.order_by(Lead.name.asc()).all()
    choices = [(lead.id, lead.name) for lead in leads]
    if include_blank:
        return [(0, "— Select lead —")] + choices
    return choices


def customer_choices(*, include_blank: bool = True) -> list[tuple[int, str]]:
    customers = Customer.query.order_by(Customer.name.asc()).all()
    choices = [(customer.id, customer.name) for customer in customers]
    if include_blank:
        return [(0, "— Select customer —")] + choices
    return choices
