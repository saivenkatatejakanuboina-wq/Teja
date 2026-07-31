"""Lead Management blueprint — CRUD, search, filter, pagination, activity log."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import LeadForm
from app.models import LEAD_SOURCES, LEAD_STATUSES, Lead, User
from app.services.activity import log_activity

leads_bp = Blueprint("leads", __name__)

PER_PAGE = 10


def _get_lead_or_404(lead_id: int) -> Lead:
    lead = db.session.get(Lead, lead_id)
    if lead is None:
        abort(404)
    return lead


def _employee_choices():
    employees = (
        User.query.filter_by(is_active=True)
        .order_by(User.full_name.asc())
        .all()
    )
    return [(0, "— Unassigned —")] + [
        (u.id, f"{u.full_name} ({u.role_label})") for u in employees
    ]


def _populate_lead_form(form: LeadForm) -> None:
    form.assigned_to_id.choices = _employee_choices()


def _apply_lead_data(lead: Lead, form: LeadForm) -> None:
    assigned_id = form.assigned_to_id.data or 0
    lead.name = form.name.data.strip()
    lead.company = form.company.data.strip() if form.company.data else None
    lead.email = form.email.data.strip().lower() if form.email.data else None
    lead.phone = form.phone.data.strip() if form.phone.data else None
    lead.country = form.country.data.strip() if form.country.data else None
    lead.industry = form.industry.data.strip() if form.industry.data else None
    lead.lead_source = form.lead_source.data
    lead.status = form.status.data
    lead.notes = form.notes.data.strip() if form.notes.data else None
    lead.assigned_to_id = assigned_id if assigned_id > 0 else None


@leads_bp.route("/")
@login_required
def index():
    """List leads with search, filter, and pagination."""
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    source = request.args.get("source", "").strip()
    assigned = request.args.get("assigned", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Lead.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Lead.name.ilike(like),
                Lead.company.ilike(like),
                Lead.email.ilike(like),
                Lead.phone.ilike(like),
                Lead.country.ilike(like),
                Lead.industry.ilike(like),
            )
        )
    if status:
        query = query.filter(Lead.status == status)
    if source:
        query = query.filter(Lead.lead_source == source)
    if assigned == "unassigned":
        query = query.filter(Lead.assigned_to_id.is_(None))
    elif assigned.isdigit():
        query = query.filter(Lead.assigned_to_id == int(assigned))

    query = query.order_by(Lead.created_at.desc())
    pagination = db.paginate(query, page=page, per_page=PER_PAGE, error_out=False)

    employees = (
        User.query.filter_by(is_active=True).order_by(User.full_name.asc()).all()
    )

    return render_template(
        "leads/index.html",
        title="Leads",
        leads=pagination.items,
        pagination=pagination,
        q=q,
        status=status,
        source=source,
        assigned=assigned,
        statuses=LEAD_STATUSES,
        sources=LEAD_SOURCES,
        employees=employees,
    )


@leads_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Add a new lead."""
    form = LeadForm()
    _populate_lead_form(form)
    if request.method == "GET" and not form.assigned_to_id.data:
        form.assigned_to_id.data = current_user.id

    if form.validate_on_submit():
        lead = Lead(created_by_id=current_user.id)
        _apply_lead_data(lead, form)
        db.session.add(lead)
        db.session.flush()
        log_activity(
            "created",
            f"Created lead “{lead.name}”",
            lead_id=lead.id,
            details=f"Status: {lead.status}; Source: {lead.lead_source}",
        )
        db.session.commit()
        flash("Lead created successfully.", "success")
        return redirect(url_for("leads.detail", lead_id=lead.id))

    return render_template("leads/form.html", form=form, title="Add Lead")


@leads_bp.route("/<int:lead_id>")
@login_required
def detail(lead_id: int):
    """Lead detail with recent activity log and email history."""
    from app.models import ActivityLog, EmailMessage

    lead = _get_lead_or_404(lead_id)
    activities = (
        ActivityLog.query.filter_by(lead_id=lead.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(20)
        .all()
    )
    emails = (
        EmailMessage.query.filter_by(lead_id=lead.id)
        .order_by(EmailMessage.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "leads/detail.html",
        lead=lead,
        activities=activities,
        emails=emails,
        title=lead.name,
    )


@leads_bp.route("/<int:lead_id>/edit", methods=["GET", "POST"])
@login_required
def edit(lead_id: int):
    """Edit an existing lead."""
    lead = _get_lead_or_404(lead_id)
    form = LeadForm(obj=lead)
    _populate_lead_form(form)

    if request.method == "GET":
        form.assigned_to_id.data = lead.assigned_to_id or 0

    if form.validate_on_submit():
        old_status = lead.status
        old_assignee = lead.assigned_to_id
        _apply_lead_data(lead, form)
        changes = []
        if old_status != lead.status:
            changes.append(f"status {old_status} → {lead.status}")
        if old_assignee != lead.assigned_to_id:
            changes.append("assignment updated")
        detail_text = "; ".join(changes) if changes else "Lead details updated"
        log_activity(
            "updated",
            f"Updated lead “{lead.name}”",
            lead_id=lead.id,
            details=detail_text,
        )
        db.session.commit()
        flash("Lead updated successfully.", "success")
        return redirect(url_for("leads.detail", lead_id=lead.id))

    return render_template(
        "leads/form.html",
        form=form,
        title="Edit Lead",
        lead=lead,
    )


@leads_bp.route("/<int:lead_id>/delete", methods=["POST"])
@login_required
def delete(lead_id: int):
    """Delete a lead after confirmation."""
    from app.models import ActivityLog

    lead = _get_lead_or_404(lead_id)
    lead_name = lead.name
    # Preserve audit trail: detach prior lead activities before delete
    ActivityLog.query.filter_by(lead_id=lead.id).update(
        {ActivityLog.lead_id: None},
        synchronize_session=False,
    )
    log_activity(
        "deleted",
        f"Deleted lead “{lead_name}”",
        lead_id=None,
        entity_type="lead",
        entity_id=lead_id,
        details=f"Company: {lead.company or '—'}; Status: {lead.status}",
    )
    db.session.delete(lead)
    db.session.commit()
    flash(f"Lead “{lead_name}” has been deleted.", "info")
    return redirect(url_for("leads.index"))
