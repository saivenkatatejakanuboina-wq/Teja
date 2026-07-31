"""Dashboard blueprint (controller)."""

from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Company, Contact, Deal

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    owner_id = current_user.id

    total_contacts = Contact.query.filter_by(owner_id=owner_id).count()
    total_companies = Company.query.filter_by(owner_id=owner_id).count()
    total_deals = Deal.query.filter_by(owner_id=owner_id).count()

    pipeline_value = (
        db.session.query(func.coalesce(func.sum(Deal.value), 0))
        .filter(
            Deal.owner_id == owner_id,
            Deal.stage.notin_(["Closed Won", "Closed Lost"]),
        )
        .scalar()
    )
    won_value = (
        db.session.query(func.coalesce(func.sum(Deal.value), 0))
        .filter(Deal.owner_id == owner_id, Deal.stage == "Closed Won")
        .scalar()
    )

    recent_contacts = (
        Contact.query.filter_by(owner_id=owner_id)
        .order_by(Contact.created_at.desc())
        .limit(5)
        .all()
    )
    recent_deals = (
        Deal.query.filter_by(owner_id=owner_id)
        .order_by(Deal.created_at.desc())
        .limit(5)
        .all()
    )

    stage_counts = (
        db.session.query(Deal.stage, func.count(Deal.id))
        .filter(Deal.owner_id == owner_id)
        .group_by(Deal.stage)
        .all()
    )
    stage_data = {stage: count for stage, count in stage_counts}

    return render_template(
        "dashboard/index.html",
        title="Dashboard",
        total_contacts=total_contacts,
        total_companies=total_companies,
        total_deals=total_deals,
        pipeline_value=pipeline_value,
        won_value=won_value,
        recent_contacts=recent_contacts,
        recent_deals=recent_deals,
        stage_data=stage_data,
    )
