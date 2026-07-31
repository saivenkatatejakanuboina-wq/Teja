"""Reports module — Chart.js dashboards and CSV export."""

import csv
import io

from flask import Blueprint, Response, abort, render_template, url_for
from flask_login import login_required

from app.services import reports as report_service

reports_bp = Blueprint("reports", __name__)

EXPORT_TYPES = {
    "monthly_leads",
    "lead_sources",
    "won_vs_lost",
    "employee_performance",
    "customer_growth",
}


@reports_bp.route("/")
@login_required
def index():
    """Reports dashboard with Chart.js visualizations."""
    data = report_service.build_all_reports()
    exports = {
        key: url_for("reports.export_csv", report_type=key) for key in EXPORT_TYPES
    }
    return render_template(
        "reports/index.html",
        title="Reports",
        reports=data,
        exports=exports,
    )


@reports_bp.route("/export/<report_type>.csv")
@login_required
def export_csv(report_type: str):
    """Export a report dataset as CSV."""
    if report_type not in EXPORT_TYPES:
        abort(404)

    data = report_service.build_all_reports()[report_type]
    rows = data.get("rows") or []

    output = io.StringIO()
    if not rows:
        writer = csv.writer(output)
        writer.writerow(["message"])
        writer.writerow(["No data available"])
    else:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    filename = f"{report_type}_report.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
