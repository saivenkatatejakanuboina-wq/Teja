"""Companies blueprint (controller)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import CompanyForm
from app.models import Company

companies_bp = Blueprint("companies", __name__)


def _get_owned_company_or_404(company_id: int) -> Company:
    company = db.session.get(Company, company_id)
    if company is None or company.owner_id != current_user.id:
        abort(404)
    return company


@companies_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    query = Company.query.filter_by(owner_id=current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Company.name.ilike(like),
                Company.industry.ilike(like),
                Company.city.ilike(like),
            )
        )
    companies = query.order_by(Company.name.asc()).all()
    return render_template(
        "companies/index.html",
        companies=companies,
        q=q,
        title="Companies",
    )


@companies_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = CompanyForm()
    if form.validate_on_submit():
        company = Company(
            name=form.name.data.strip(),
            industry=form.industry.data.strip() if form.industry.data else None,
            website=form.website.data.strip() if form.website.data else None,
            phone=form.phone.data.strip() if form.phone.data else None,
            email=form.email.data.strip() if form.email.data else None,
            address=form.address.data.strip() if form.address.data else None,
            city=form.city.data.strip() if form.city.data else None,
            country=form.country.data.strip() if form.country.data else None,
            notes=form.notes.data.strip() if form.notes.data else None,
            owner_id=current_user.id,
        )
        db.session.add(company)
        db.session.commit()
        flash("Company created successfully.", "success")
        return redirect(url_for("companies.index"))
    return render_template("companies/form.html", form=form, title="New Company")


@companies_bp.route("/<int:company_id>")
@login_required
def detail(company_id: int):
    company = _get_owned_company_or_404(company_id)
    return render_template(
        "companies/detail.html",
        company=company,
        title=company.name,
    )


@companies_bp.route("/<int:company_id>/edit", methods=["GET", "POST"])
@login_required
def edit(company_id: int):
    company = _get_owned_company_or_404(company_id)
    form = CompanyForm(obj=company)
    if form.validate_on_submit():
        company.name = form.name.data.strip()
        company.industry = form.industry.data.strip() if form.industry.data else None
        company.website = form.website.data.strip() if form.website.data else None
        company.phone = form.phone.data.strip() if form.phone.data else None
        company.email = form.email.data.strip() if form.email.data else None
        company.address = form.address.data.strip() if form.address.data else None
        company.city = form.city.data.strip() if form.city.data else None
        company.country = form.country.data.strip() if form.country.data else None
        company.notes = form.notes.data.strip() if form.notes.data else None
        db.session.commit()
        flash("Company updated successfully.", "success")
        return redirect(url_for("companies.detail", company_id=company.id))
    return render_template("companies/form.html", form=form, title="Edit Company", company=company)


@companies_bp.route("/<int:company_id>/delete", methods=["POST"])
@login_required
def delete(company_id: int):
    company = _get_owned_company_or_404(company_id)
    for contact in company.contacts.all():
        contact.company_id = None
    for deal in company.deals.all():
        deal.company_id = None
    db.session.delete(company)
    db.session.commit()
    flash("Company deleted.", "info")
    return redirect(url_for("companies.index"))
