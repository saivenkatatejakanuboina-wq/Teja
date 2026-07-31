"""Follow-up Management — schedule, list buckets, and calendar view."""

from calendar import Calendar, month_name
from datetime import date, datetime, time, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import FollowUpForm
from app.models import FOLLOWUP_TYPES, FollowUp
from app.services.activity import log_activity
from app.utils.db import get_or_404

followups_bp = Blueprint("followups", __name__)


def _get_followup_or_404(followup_id: int) -> FollowUp:
    return get_or_404(FollowUp, followup_id)


def _populate_form(form: FollowUpForm) -> None:
    from app.services.choices import customer_choices, employee_choices, lead_choices

    form.assigned_to_id.choices = employee_choices(include_unassigned=False)
    form.lead_id.choices = [(0, "— None —")] + [
        (lid, name) for lid, name in lead_choices(include_blank=False)
    ]
    form.customer_id.choices = [(0, "— None —")] + [
        (cid, name) for cid, name in customer_choices(include_blank=False)
    ]


def _apply_form_data(followup: FollowUp, form: FollowUpForm) -> None:
    followup.title = form.title.data.strip()
    followup.followup_type = form.followup_type.data
    followup.reminder_date = form.reminder_date.data
    followup.reminder_time = form.reminder_time.data
    followup.status = form.status.data
    followup.remarks = form.remarks.data.strip() if form.remarks.data else None
    followup.assigned_to_id = form.assigned_to_id.data
    lead_id = form.lead_id.data or 0
    customer_id = form.customer_id.data or 0
    followup.lead_id = lead_id if lead_id > 0 else None
    followup.customer_id = customer_id if customer_id > 0 else None


def _sync_missed_statuses() -> None:
    """Mark overdue Scheduled follow-ups as Missed (bulk SQL, no row-by-row load)."""
    now = datetime.now()
    today = now.date()
    current_time = now.time()
    updated = FollowUp.query.filter(
        FollowUp.status == "Scheduled",
        db.or_(
            FollowUp.reminder_date < today,
            db.and_(
                FollowUp.reminder_date == today,
                FollowUp.reminder_time < current_time,
            ),
        ),
    ).update({FollowUp.status: "Missed"}, synchronize_session=False)
    if updated:
        db.session.commit()


def _bucket_counts() -> dict:
    today = date.today()
    base = FollowUp.query
    today_count = base.filter(
        FollowUp.reminder_date == today,
        FollowUp.status.in_(["Scheduled", "Missed", "Completed"]),
    ).count()
    upcoming_count = base.filter(
        FollowUp.reminder_date > today,
        FollowUp.status == "Scheduled",
    ).count()
    missed_count = base.filter(FollowUp.status == "Missed").count()
    return {
        "today": today_count,
        "upcoming": upcoming_count,
        "missed": missed_count,
        "all": base.count(),
    }


@followups_bp.route("/")
@login_required
def index():
    """List follow-ups by bucket: today / upcoming / missed / all."""
    _sync_missed_statuses()

    view = request.args.get("view", "today").strip().lower()
    followup_type = request.args.get("type", "").strip()
    q = request.args.get("q", "").strip()
    today = date.today()

    from sqlalchemy.orm import joinedload

    query = FollowUp.query.options(
        joinedload(FollowUp.assigned_to),
        joinedload(FollowUp.lead),
        joinedload(FollowUp.customer),
    )
    if view == "today":
        query = query.filter(FollowUp.reminder_date == today)
    elif view == "upcoming":
        query = query.filter(
            FollowUp.reminder_date > today,
            FollowUp.status == "Scheduled",
        )
    elif view == "missed":
        query = query.filter(FollowUp.status == "Missed")
    # else: all

    if followup_type:
        query = query.filter(FollowUp.followup_type == followup_type)
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                FollowUp.title.ilike(like),
                FollowUp.remarks.ilike(like),
            )
        )

    followups = query.order_by(
        FollowUp.reminder_date.asc(),
        FollowUp.reminder_time.asc(),
    ).all()

    return render_template(
        "followups/index.html",
        title="Follow-ups",
        followups=followups,
        view=view,
        followup_type=followup_type,
        q=q,
        types=FOLLOWUP_TYPES,
        counts=_bucket_counts(),
    )


@followups_bp.route("/calendar")
@login_required
def calendar():
    """Bootstrap month calendar view of follow-ups."""
    _sync_missed_statuses()

    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    items = (
        FollowUp.query.filter(
            FollowUp.reminder_date >= month_start,
            FollowUp.reminder_date <= month_end,
        )
        .order_by(FollowUp.reminder_time.asc())
        .all()
    )

    by_day: dict[str, list] = {}
    for item in items:
        key = item.reminder_date.isoformat()
        by_day.setdefault(key, []).append(
            {
                "id": item.id,
                "title": item.title,
                "type": item.followup_type,
                "time": item.reminder_time.strftime("%H:%M"),
                "status": item.effective_status,
                "url": url_for("followups.detail", followup_id=item.id),
            }
        )

    cal = Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(year, month)

    prev_month = month - 1 or 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    return render_template(
        "followups/calendar.html",
        title="Follow-up Calendar",
        year=year,
        month=month,
        month_label=f"{month_name[month]} {year}",
        weeks=weeks,
        by_day=by_day,
        today=today,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        counts=_bucket_counts(),
    )


@followups_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Schedule a new follow-up."""
    form = FollowUpForm()
    _populate_form(form)

    if request.method == "GET":
        form.assigned_to_id.data = current_user.id
        form.reminder_date.data = date.today()
        form.reminder_time.data = time(10, 0)
        form.status.data = "Scheduled"
        form.lead_id.data = request.args.get("lead_id", 0, type=int)
        form.customer_id.data = request.args.get("customer_id", 0, type=int)

    if form.validate_on_submit():
        followup = FollowUp(created_by_id=current_user.id)
        _apply_form_data(followup, form)
        if followup.is_overdue and followup.status == "Scheduled":
            followup.status = "Missed"
        db.session.add(followup)
        db.session.flush()
        log_activity(
            "created",
            f"Scheduled {followup.followup_type.lower()} follow-up “{followup.title}”",
            lead_id=followup.lead_id,
            customer_id=followup.customer_id,
            entity_type="followup",
            entity_id=followup.id,
            details=(
                f"{followup.reminder_date.isoformat()} "
                f"{followup.reminder_time.strftime('%H:%M')} · {followup.status}"
            ),
        )
        db.session.commit()
        flash("Follow-up scheduled successfully.", "success")
        return redirect(url_for("followups.detail", followup_id=followup.id))

    return render_template(
        "followups/form.html",
        form=form,
        title="Schedule Follow-up",
    )


@followups_bp.route("/<int:followup_id>")
@login_required
def detail(followup_id: int):
    followup = _get_followup_or_404(followup_id)
    if followup.status == "Scheduled" and followup.is_overdue:
        followup.status = "Missed"
        db.session.commit()
    return render_template(
        "followups/detail.html",
        followup=followup,
        title=followup.title,
    )


@followups_bp.route("/<int:followup_id>/edit", methods=["GET", "POST"])
@login_required
def edit(followup_id: int):
    followup = _get_followup_or_404(followup_id)
    form = FollowUpForm(obj=followup)
    _populate_form(form)

    if request.method == "GET":
        form.lead_id.data = followup.lead_id or 0
        form.customer_id.data = followup.customer_id or 0
        form.assigned_to_id.data = followup.assigned_to_id

    if form.validate_on_submit():
        _apply_form_data(followup, form)
        if followup.status == "Scheduled" and followup.is_overdue:
            followup.status = "Missed"
        log_activity(
            "updated",
            f"Updated follow-up “{followup.title}”",
            lead_id=followup.lead_id,
            customer_id=followup.customer_id,
            entity_type="followup",
            entity_id=followup.id,
            details=f"Status: {followup.status}",
        )
        db.session.commit()
        flash("Follow-up updated successfully.", "success")
        return redirect(url_for("followups.detail", followup_id=followup.id))

    return render_template(
        "followups/form.html",
        form=form,
        title="Edit Follow-up",
        followup=followup,
    )


@followups_bp.route("/<int:followup_id>/complete", methods=["POST"])
@login_required
def complete(followup_id: int):
    followup = _get_followup_or_404(followup_id)
    followup.status = "Completed"
    log_activity(
        "completed",
        f"Completed follow-up “{followup.title}”",
        lead_id=followup.lead_id,
        customer_id=followup.customer_id,
        entity_type="followup",
        entity_id=followup.id,
    )
    db.session.commit()
    flash("Follow-up marked as completed.", "success")
    from app.utils.security import safe_referrer_or

    return redirect(safe_referrer_or(url_for("followups.index", view="today")))


@followups_bp.route("/<int:followup_id>/delete", methods=["POST"])
@login_required
def delete(followup_id: int):
    followup = _get_followup_or_404(followup_id)
    title = followup.title
    log_activity(
        "deleted",
        f"Deleted follow-up “{title}”",
        entity_type="followup",
        entity_id=followup_id,
        details=f"Type: {followup.followup_type}; Date: {followup.reminder_date}",
    )
    db.session.delete(followup)
    db.session.commit()
    flash(f"Follow-up “{title}” deleted.", "info")
    return redirect(url_for("followups.index", view="today"))
