"""Contacts blueprint (controller)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import ContactForm
from app.models import Company, Contact

contacts_bp = Blueprint("contacts", __name__)


def _get_owned_contact_or_404(contact_id: int) -> Contact:
    contact = db.session.get(Contact, contact_id)
    if contact is None or contact.owner_id != current_user.id:
        abort(404)
    return contact


def _company_choices():
    companies = (
        Company.query.filter_by(owner_id=current_user.id)
        .order_by(Company.name.asc())
        .all()
    )
    return [(0, "— None —")] + [(c.id, c.name) for c in companies]


@contacts_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    query = Contact.query.filter_by(owner_id=current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Contact.first_name.ilike(like),
                Contact.last_name.ilike(like),
                Contact.email.ilike(like),
                Contact.job_title.ilike(like),
            )
        )
    if status:
        query = query.filter_by(status=status)
    contacts = query.order_by(Contact.last_name.asc(), Contact.first_name.asc()).all()
    return render_template(
        "contacts/index.html",
        contacts=contacts,
        q=q,
        status=status,
        title="Contacts",
    )


@contacts_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = ContactForm()
    form.company_id.choices = _company_choices()
    if form.validate_on_submit():
        company_id = form.company_id.data or 0
        contact = Contact(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=form.email.data.strip() if form.email.data else None,
            phone=form.phone.data.strip() if form.phone.data else None,
            job_title=form.job_title.data.strip() if form.job_title.data else None,
            status=form.status.data,
            notes=form.notes.data.strip() if form.notes.data else None,
            company_id=company_id if company_id > 0 else None,
            owner_id=current_user.id,
        )
        db.session.add(contact)
        db.session.commit()
        flash("Contact created successfully.", "success")
        return redirect(url_for("contacts.index"))
    return render_template("contacts/form.html", form=form, title="New Contact")


@contacts_bp.route("/<int:contact_id>")
@login_required
def detail(contact_id: int):
    contact = _get_owned_contact_or_404(contact_id)
    return render_template(
        "contacts/detail.html",
        contact=contact,
        title=contact.full_name,
    )


@contacts_bp.route("/<int:contact_id>/edit", methods=["GET", "POST"])
@login_required
def edit(contact_id: int):
    contact = _get_owned_contact_or_404(contact_id)
    form = ContactForm(obj=contact)
    form.company_id.choices = _company_choices()
    if request.method == "GET":
        form.company_id.data = contact.company_id or 0
    if form.validate_on_submit():
        company_id = form.company_id.data or 0
        contact.first_name = form.first_name.data.strip()
        contact.last_name = form.last_name.data.strip()
        contact.email = form.email.data.strip() if form.email.data else None
        contact.phone = form.phone.data.strip() if form.phone.data else None
        contact.job_title = form.job_title.data.strip() if form.job_title.data else None
        contact.status = form.status.data
        contact.notes = form.notes.data.strip() if form.notes.data else None
        contact.company_id = company_id if company_id > 0 else None
        db.session.commit()
        flash("Contact updated successfully.", "success")
        return redirect(url_for("contacts.detail", contact_id=contact.id))
    return render_template(
        "contacts/form.html",
        form=form,
        title="Edit Contact",
        contact=contact,
    )


@contacts_bp.route("/<int:contact_id>/delete", methods=["POST"])
@login_required
def delete(contact_id: int):
    contact = _get_owned_contact_or_404(contact_id)
    for deal in contact.deals.all():
        deal.contact_id = None
    db.session.delete(contact)
    db.session.commit()
    flash("Contact deleted.", "info")
    return redirect(url_for("contacts.index"))
