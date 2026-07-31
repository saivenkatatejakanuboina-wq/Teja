"""Activity Log blueprint — browse tracked CRM and auth events."""

from __future__ import annotations

from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_

from app.models import TRACKED_ACTIVITY_FILTERS, ActivityLog, User
from app.services.activity import activity_filter_clause

activities_bp = Blueprint("activities", __name__, url_prefix="/activities")


@activities_bp.route("/")
@login_required
def index():
    from sqlalchemy.orm import joinedload

    from app.utils.pagination import paginate

    q = (request.args.get("q") or "").strip()
    action_filter = (request.args.get("action") or "").strip()
    user_id = request.args.get("user_id", type=int)

    query = ActivityLog.query.options(joinedload(ActivityLog.user))
    mapped = activity_filter_clause(action_filter)
    if mapped:
        action_name, entity_type = mapped
        query = query.filter(
            ActivityLog.action == action_name,
            ActivityLog.entity_type == entity_type,
        )

    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)

    if q:
        like = f"%{q}%"
        query = query.outerjoin(User, ActivityLog.user_id == User.id).filter(
            or_(
                ActivityLog.message.ilike(like),
                ActivityLog.details.ilike(like),
                ActivityLog.ip_address.ilike(like),
                ActivityLog.action.ilike(like),
                User.full_name.ilike(like),
                User.username.ilike(like),
            )
        )

    pagination = paginate(
        query.order_by(ActivityLog.created_at.desc()),
        per_page=20,
    )

    users = User.query.order_by(User.full_name.asc()).all()

    return render_template(
        "activities/index.html",
        title="Activity Log",
        activities=pagination.items,
        pagination=pagination,
        q=q,
        action=action_filter,
        user_id=user_id,
        users=users,
        action_filters=TRACKED_ACTIVITY_FILTERS,
    )
