"""Deals blueprint (controller)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import DealForm
from app.models import Company, Contact, Deal

deals_bp = Blueprint("deals", __name__)


def _get_owned_deal_or_404(deal_id: int) -> Deal:
    deal = db.session.get(Deal, deal_id)
    if deal is None or deal.owner_id != current_user.id:
        abort(404)
    return deal


def _populate_deal_choices(form: DealForm) -> None:
    companies = (
        Company.query.filter_by(owner_id=current_user.id)
        .order_by(Company.name.asc())
        .all()
    )
    contacts = (
        Contact.query.filter_by(owner_id=current_user.id)
        .order_by(Contact.last_name.asc())
        .all()
    )
    form.company_id.choices = [(0, "— None —")] + [(c.id, c.name) for c in companies]
    form.contact_id.choices = [(0, "— None —")] + [
        (c.id, c.full_name) for c in contacts
    ]


@deals_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    stage = request.args.get("stage", "").strip()
    query = Deal.query.filter_by(owner_id=current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(Deal.title.ilike(like))
    if stage:
        query = query.filter_by(stage=stage)
    deals = query.order_by(Deal.created_at.desc()).all()
    return render_template(
        "deals/index.html",
        deals=deals,
        q=q,
        stage=stage,
        title="Deals",
    )


@deals_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = DealForm()
    _populate_deal_choices(form)
    if form.validate_on_submit():
        company_id = form.company_id.data or 0
        contact_id = form.contact_id.data or 0
        deal = Deal(
            title=form.title.data.strip(),
            value=form.value.data,
            stage=form.stage.data,
            probability=form.probability.data,
            expected_close_date=form.expected_close_date.data,
            notes=form.notes.data.strip() if form.notes.data else None,
            company_id=company_id if company_id > 0 else None,
            contact_id=contact_id if contact_id > 0 else None,
            owner_id=current_user.id,
        )
        db.session.add(deal)
        db.session.commit()
        flash("Deal created successfully.", "success")
        return redirect(url_for("deals.index"))
    return render_template("deals/form.html", form=form, title="New Deal")


@deals_bp.route("/<int:deal_id>")
@login_required
def detail(deal_id: int):
    deal = _get_owned_deal_or_404(deal_id)
    return render_template("deals/detail.html", deal=deal, title=deal.title)


@deals_bp.route("/<int:deal_id>/edit", methods=["GET", "POST"])
@login_required
def edit(deal_id: int):
    deal = _get_owned_deal_or_404(deal_id)
    form = DealForm(obj=deal)
    _populate_deal_choices(form)
    if request.method == "GET":
        form.company_id.data = deal.company_id or 0
        form.contact_id.data = deal.contact_id or 0
    if form.validate_on_submit():
        company_id = form.company_id.data or 0
        contact_id = form.contact_id.data or 0
        deal.title = form.title.data.strip()
        deal.value = form.value.data
        deal.stage = form.stage.data
        deal.probability = form.probability.data
        deal.expected_close_date = form.expected_close_date.data
        deal.notes = form.notes.data.strip() if form.notes.data else None
        deal.company_id = company_id if company_id > 0 else None
        deal.contact_id = contact_id if contact_id > 0 else None
        db.session.commit()
        flash("Deal updated successfully.", "success")
        return redirect(url_for("deals.detail", deal_id=deal.id))
    return render_template("deals/form.html", form=form, title="Edit Deal", deal=deal)


@deals_bp.route("/<int:deal_id>/delete", methods=["POST"])
@login_required
def delete(deal_id: int):
    deal = _get_owned_deal_or_404(deal_id)
    db.session.delete(deal)
    db.session.commit()
    flash("Deal deleted.", "info")
    return redirect(url_for("deals.index"))
