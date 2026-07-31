"""Customer Management blueprint — CRUD, search, pagination, lead conversion."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import CustomerForm
from app.models import ActivityLog, Customer, Lead
from app.services.activity import log_activity

customers_bp = Blueprint("customers", __name__)

PER_PAGE = 10


def _get_customer_or_404(customer_id: int) -> Customer:
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        abort(404)
    return customer


def _apply_customer_data(customer: Customer, form: CustomerForm) -> None:
    customer.name = form.name.data.strip()
    customer.primary_contact = (
        form.primary_contact.data.strip() if form.primary_contact.data else None
    )
    customer.email = form.email.data.strip().lower() if form.email.data else None
    customer.phone = form.phone.data.strip() if form.phone.data else None
    customer.address = form.address.data.strip() if form.address.data else None
    customer.gst = form.gst.data.strip().upper() if form.gst.data else None
    customer.website = form.website.data.strip() if form.website.data else None
    customer.industry = form.industry.data.strip() if form.industry.data else None
    customer.country = form.country.data.strip() if form.country.data else None
    customer.status = form.status.data
    customer.notes = form.notes.data.strip() if form.notes.data else None


@customers_bp.route("/")
@login_required
def index():
    """Customer list with search and pagination."""
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Customer.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Customer.name.ilike(like),
                Customer.primary_contact.ilike(like),
                Customer.email.ilike(like),
                Customer.phone.ilike(like),
                Customer.gst.ilike(like),
                Customer.industry.ilike(like),
                Customer.address.ilike(like),
            )
        )
    if status:
        query = query.filter(Customer.status == status)

    query = query.order_by(Customer.created_at.desc())
    pagination = db.paginate(query, page=page, per_page=PER_PAGE, error_out=False)

    return render_template(
        "customers/index.html",
        title="Customers",
        customers=pagination.items,
        pagination=pagination,
        q=q,
        status=status,
    )


@customers_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Add a customer manually."""
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(owner_id=current_user.id)
        _apply_customer_data(customer, form)
        db.session.add(customer)
        db.session.flush()
        log_activity(
            "created",
            f"Created customer “{customer.name}”",
            customer_id=customer.id,
            entity_type="customer",
            entity_id=customer.id,
            details=f"Status: {customer.status}",
        )
        db.session.commit()
        flash("Customer created successfully.", "success")
        return redirect(url_for("customers.detail", customer_id=customer.id))

    return render_template("customers/form.html", form=form, title="Add Customer")


@customers_bp.route("/<int:customer_id>")
@login_required
def detail(customer_id: int):
    """Customer details page."""
    customer = _get_customer_or_404(customer_id)
    activities = (
        ActivityLog.query.filter(
            db.or_(
                ActivityLog.customer_id == customer.id,
                db.and_(
                    ActivityLog.entity_type == "customer",
                    ActivityLog.entity_id == customer.id,
                ),
            )
        )
        .order_by(ActivityLog.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "customers/detail.html",
        customer=customer,
        activities=activities,
        title=customer.name,
    )


@customers_bp.route("/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
def edit(customer_id: int):
    """Edit customer details."""
    customer = _get_customer_or_404(customer_id)
    form = CustomerForm(obj=customer)

    if form.validate_on_submit():
        _apply_customer_data(customer, form)
        log_activity(
            "updated",
            f"Updated customer “{customer.name}”",
            customer_id=customer.id,
            entity_type="customer",
            entity_id=customer.id,
            details=f"Status: {customer.status}",
        )
        db.session.commit()
        flash("Customer updated successfully.", "success")
        return redirect(url_for("customers.detail", customer_id=customer.id))

    return render_template(
        "customers/form.html",
        form=form,
        title="Edit Customer",
        customer=customer,
    )


@customers_bp.route("/<int:customer_id>/delete", methods=["POST"])
@login_required
def delete(customer_id: int):
    """Delete a customer."""
    customer = _get_customer_or_404(customer_id)
    name = customer.name
    # Preserve audit trail: detach prior customer activities before delete
    ActivityLog.query.filter_by(customer_id=customer.id).update(
        {ActivityLog.customer_id: None},
        synchronize_session=False,
    )
    log_activity(
        "deleted",
        f"Deleted customer “{name}”",
        customer_id=None,
        entity_type="customer",
        entity_id=customer_id,
        details=f"GST: {customer.gst or '—'}; Industry: {customer.industry or '—'}",
    )
    db.session.delete(customer)
    db.session.commit()
    flash(f"Customer “{name}” has been deleted.", "info")
    return redirect(url_for("customers.index"))


@customers_bp.route("/convert/<int:lead_id>", methods=["GET", "POST"])
@login_required
def convert_from_lead(lead_id: int):
    """Convert a Lead into a Customer."""
    lead = db.session.get(Lead, lead_id)
    if lead is None:
        abort(404)

    if lead.is_converted:
        flash("This lead has already been converted to a customer.", "warning")
        return redirect(url_for("customers.detail", customer_id=lead.customer.id))

    form = CustomerForm()
    if request.method == "GET":
        form.name.data = lead.company or lead.name
        form.primary_contact.data = lead.name
        form.email.data = lead.email
        form.phone.data = lead.phone
        form.industry.data = lead.industry
        form.country.data = lead.country
        form.notes.data = lead.notes
        form.status.data = "Active"

    if form.validate_on_submit():
        customer = Customer(owner_id=current_user.id, lead_id=lead.id)
        _apply_customer_data(customer, form)
        lead.status = "Won"
        db.session.add(customer)
        db.session.flush()
        log_activity(
            "converted",
            f"Converted lead “{lead.name}” to customer “{customer.name}”",
            lead_id=lead.id,
            customer_id=customer.id,
            entity_type="customer",
            entity_id=customer.id,
            details=f"From lead #{lead.id}",
        )
        db.session.commit()
        flash("Lead converted to customer successfully.", "success")
        return redirect(url_for("customers.detail", customer_id=customer.id))

    return render_template(
        "customers/form.html",
        form=form,
        title="Convert Lead to Customer",
        lead=lead,
        converting=True,
    )
