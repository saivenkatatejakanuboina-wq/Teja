"""CSV Import / Export for Leads and Customers."""

from __future__ import annotations

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import login_required

from app.forms import CSVImportForm
from app.models import LEAD_SOURCES, LEAD_STATUSES
from app.services import csv_io as csv_service

csv_bp = Blueprint("csv_io", __name__, url_prefix="/csv")


@csv_bp.route("/")
@login_required
def index():
    lead_form = CSVImportForm(prefix="leads")
    customer_form = CSVImportForm(prefix="customers")
    return render_template(
        "csv/index.html",
        title="CSV Import / Export",
        lead_form=lead_form,
        customer_form=customer_form,
        lead_errors=None,
        customer_errors=None,
        lead_columns=csv_service.LEAD_FIELDNAMES,
        customer_columns=csv_service.CUSTOMER_FIELDNAMES,
        lead_sources=LEAD_SOURCES,
        lead_statuses=LEAD_STATUSES,
        active_tab="leads",
    )


@csv_bp.route("/leads/import", methods=["POST"])
@login_required
def import_leads():
    form = CSVImportForm(prefix="leads")
    customer_form = CSVImportForm(prefix="customers")
    lead_errors = None

    if form.validate_on_submit():
        result = csv_service.validate_leads_csv(form.csv_file.data)
        if not result.valid:
            lead_errors = result.errors
            flash(
                f"Lead CSV validation failed with {len(result.errors)} error(s). "
                "Nothing was imported.",
                "danger",
            )
        else:
            count = csv_service.import_leads(result.rows)
            flash(f"Successfully imported {count} lead(s).", "success")
            return redirect(url_for("csv_io.index"))
    else:
        flash("Please upload a valid .csv file for leads.", "danger")
        lead_errors = [
            csv_service.RowError(0, field, "; ".join(errs))
            for field, errs in form.errors.items()
        ]

    return render_template(
        "csv/index.html",
        title="CSV Import / Export",
        lead_form=form,
        customer_form=customer_form,
        lead_errors=lead_errors,
        customer_errors=None,
        lead_columns=csv_service.LEAD_FIELDNAMES,
        customer_columns=csv_service.CUSTOMER_FIELDNAMES,
        lead_sources=LEAD_SOURCES,
        lead_statuses=LEAD_STATUSES,
        active_tab="leads",
    )


@csv_bp.route("/customers/import", methods=["POST"])
@login_required
def import_customers():
    form = CSVImportForm(prefix="customers")
    lead_form = CSVImportForm(prefix="leads")
    customer_errors = None

    if form.validate_on_submit():
        result = csv_service.validate_customers_csv(form.csv_file.data)
        if not result.valid:
            customer_errors = result.errors
            flash(
                f"Customer CSV validation failed with {len(result.errors)} error(s). "
                "Nothing was imported.",
                "danger",
            )
        else:
            count = csv_service.import_customers(result.rows)
            flash(f"Successfully imported {count} customer(s).", "success")
            return redirect(url_for("csv_io.index"))
    else:
        flash("Please upload a valid .csv file for customers.", "danger")
        customer_errors = [
            csv_service.RowError(0, field, "; ".join(errs))
            for field, errs in form.errors.items()
        ]

    return render_template(
        "csv/index.html",
        title="CSV Import / Export",
        lead_form=lead_form,
        customer_form=form,
        lead_errors=None,
        customer_errors=customer_errors,
        lead_columns=csv_service.LEAD_FIELDNAMES,
        customer_columns=csv_service.CUSTOMER_FIELDNAMES,
        lead_sources=LEAD_SOURCES,
        lead_statuses=LEAD_STATUSES,
        active_tab="customers",
    )


@csv_bp.route("/leads/export")
@login_required
def export_leads():
    payload = csv_service.export_leads_csv()
    return Response(
        payload,
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leads_export.csv"'},
    )


@csv_bp.route("/customers/export")
@login_required
def export_customers():
    payload = csv_service.export_customers_csv()
    return Response(
        payload,
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="customers_export.csv"'},
    )


@csv_bp.route("/leads/sample")
@login_required
def sample_leads():
    return Response(
        csv_service.sample_leads_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leads_sample.csv"'},
    )


@csv_bp.route("/customers/sample")
@login_required
def sample_customers():
    return Response(
        csv_service.sample_customers_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="customers_sample.csv"'},
    )
