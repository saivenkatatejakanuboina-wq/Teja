"""Report aggregation helpers for Chart.js and CSV export."""

from __future__ import annotations

from calendar import month_abbr
from datetime import datetime, timezone

from sqlalchemy import func

from app.extensions import db
from app.models import Customer, Deal, Lead, Task, User


def _month_keys(months: int = 12) -> list[str]:
    """Return YYYY-MM keys for the last N months (oldest → newest)."""
    today = datetime.now(timezone.utc).date().replace(day=1)
    keys = []
    year, month = today.year, today.month
    for _ in range(months):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    keys.reverse()
    return keys


def _label_for_month_key(key: str) -> str:
    year, month = key.split("-")
    return f"{month_abbr[int(month)]} {year}"


def monthly_leads(months: int = 12) -> dict:
    keys = _month_keys(months)
    rows = (
        db.session.query(
            func.strftime("%Y-%m", Lead.created_at).label("ym"),
            func.count(Lead.id),
        )
        .group_by("ym")
        .all()
    )
    counts = {ym: count for ym, count in rows if ym}
    values = [counts.get(k, 0) for k in keys]
    return {
        "labels": [_label_for_month_key(k) for k in keys],
        "values": values,
        "keys": keys,
        "rows": [{"month": _label_for_month_key(k), "leads": counts.get(k, 0)} for k in keys],
    }


def lead_sources() -> dict:
    rows = (
        db.session.query(Lead.lead_source, func.count(Lead.id))
        .group_by(Lead.lead_source)
        .order_by(func.count(Lead.id).desc())
        .all()
    )
    labels = [r[0] or "Unknown" for r in rows]
    values = [r[1] for r in rows]
    if not labels:
        labels, values = ["No data"], [0]
    return {
        "labels": labels,
        "values": values,
        "rows": [{"source": l, "count": v} for l, v in zip(labels, values)],
    }


def won_vs_lost() -> dict:
    """Compare won vs lost for leads and deals."""
    lead_won = Lead.query.filter_by(status="Won").count()
    lead_lost = Lead.query.filter_by(status="Lost").count()
    deal_won = Deal.query.filter_by(stage="Closed Won").count()
    deal_lost = Deal.query.filter_by(stage="Closed Lost").count()

    return {
        "labels": ["Won", "Lost"],
        "leads": [lead_won, lead_lost],
        "deals": [deal_won, deal_lost],
        "totals": [lead_won + deal_won, lead_lost + deal_lost],
        "rows": [
            {
                "category": "Leads",
                "won": lead_won,
                "lost": lead_lost,
            },
            {
                "category": "Deals",
                "won": deal_won,
                "lost": deal_lost,
            },
            {
                "category": "Combined",
                "won": lead_won + deal_won,
                "lost": lead_lost + deal_lost,
            },
        ],
    }


def employee_performance() -> dict:
    users = User.query.filter_by(is_active=True).order_by(User.full_name.asc()).all()
    labels = []
    leads_assigned = []
    leads_won = []
    customers = []
    tasks_done = []
    deals_won = []
    rows = []

    for user in users:
        assigned = Lead.query.filter_by(assigned_to_id=user.id).count()
        won = Lead.query.filter_by(assigned_to_id=user.id, status="Won").count()
        cust = Customer.query.filter_by(owner_id=user.id).count()
        tasks = Task.query.filter_by(assigned_to_id=user.id, status="Completed").count()
        deals = Deal.query.filter_by(owner_id=user.id, stage="Closed Won").count()

        labels.append(user.full_name)
        leads_assigned.append(assigned)
        leads_won.append(won)
        customers.append(cust)
        tasks_done.append(tasks)
        deals_won.append(deals)
        rows.append(
            {
                "employee": user.full_name,
                "role": user.role_label,
                "leads_assigned": assigned,
                "leads_won": won,
                "customers": cust,
                "tasks_completed": tasks,
                "deals_won": deals,
            }
        )

    if not labels:
        labels = ["No employees"]
        leads_assigned = leads_won = customers = tasks_done = deals_won = [0]

    return {
        "labels": labels,
        "leads_assigned": leads_assigned,
        "leads_won": leads_won,
        "customers": customers,
        "tasks_completed": tasks_done,
        "deals_won": deals_won,
        "rows": rows,
    }


def customer_growth(months: int = 12) -> dict:
    keys = _month_keys(months)
    rows = (
        db.session.query(
            func.strftime("%Y-%m", Customer.created_at).label("ym"),
            func.count(Customer.id),
        )
        .group_by("ym")
        .all()
    )
    monthly = {ym: count for ym, count in rows if ym}

    # customers created before the window (for cumulative baseline)
    first_key = keys[0]
    baseline = Customer.query.filter(
        func.strftime("%Y-%m", Customer.created_at) < first_key
    ).count()

    new_values = []
    cumulative = []
    running = baseline
    for key in keys:
        added = monthly.get(key, 0)
        running += added
        new_values.append(added)
        cumulative.append(running)

    return {
        "labels": [_label_for_month_key(k) for k in keys],
        "new_customers": new_values,
        "cumulative": cumulative,
        "keys": keys,
        "rows": [
            {
                "month": _label_for_month_key(k),
                "new_customers": new_values[i],
                "cumulative": cumulative[i],
            }
            for i, k in enumerate(keys)
        ],
    }


def build_all_reports() -> dict:
    return {
        "monthly_leads": monthly_leads(),
        "lead_sources": lead_sources(),
        "won_vs_lost": won_vs_lost(),
        "employee_performance": employee_performance(),
        "customer_growth": customer_growth(),
    }
