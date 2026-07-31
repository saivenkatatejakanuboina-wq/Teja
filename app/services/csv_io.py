"""CSV import / export helpers for Leads and Customers."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from flask_login import current_user
from werkzeug.datastructures import FileStorage

from app.extensions import db
from app.models import LEAD_SOURCES, LEAD_STATUSES, Customer, Lead, User
from app.services.activity import log_activity

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

LEAD_FIELDNAMES = [
    "name",
    "company",
    "email",
    "phone",
    "country",
    "industry",
    "lead_source",
    "status",
    "notes",
    "assigned_to",
]

CUSTOMER_FIELDNAMES = [
    "name",
    "email",
    "phone",
    "address",
    "gst",
    "website",
    "industry",
    "primary_contact",
    "country",
    "status",
    "notes",
]

CUSTOMER_STATUSES = {"Active", "Inactive"}
LEAD_SOURCE_SET = {s.lower(): s for s in LEAD_SOURCES}
LEAD_STATUS_SET = {s.lower(): s for s in LEAD_STATUSES}


@dataclass
class RowError:
    row: int
    field: str
    message: str


@dataclass
class ValidationResult:
    valid: bool
    errors: list[RowError] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    headers: list[str] = field(default_factory=list)


def _normalize_header(value: str) -> str:
    return (value or "").strip().lower().replace(" ", "_")


def _cell(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def _read_csv_file(file_storage: FileStorage) -> tuple[list[str], list[dict[str, str]], list[RowError]]:
    errors: list[RowError] = []
    if not file_storage or not file_storage.filename:
        errors.append(RowError(0, "file", "Please choose a CSV file to upload."))
        return [], [], errors

    filename = file_storage.filename.lower()
    if not filename.endswith(".csv"):
        errors.append(RowError(0, "file", "Only .csv files are allowed."))
        return [], [], errors

    raw = file_storage.read()
    if not raw:
        errors.append(RowError(0, "file", "The CSV file is empty."))
        return [], [], errors

    # Reset pointer for any later re-reads
    try:
        file_storage.stream.seek(0)
    except Exception:  # noqa: BLE001
        pass

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except UnicodeDecodeError:
            errors.append(RowError(0, "file", "Could not decode the file. Use UTF-8 CSV encoding."))
            return [], [], errors

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        errors.append(RowError(0, "file", "CSV header row is missing."))
        return [], [], errors

    headers = [_normalize_header(h) for h in reader.fieldnames if h is not None]
    if any(not h for h in headers):
        errors.append(RowError(0, "file", "CSV contains an empty header column."))
        return headers, [], errors

    rows: list[dict[str, str]] = []
    for index, raw_row in enumerate(reader, start=2):  # header is row 1
        normalized = {
            _normalize_header(k): (v or "").strip() if v is not None else ""
            for k, v in raw_row.items()
            if k is not None
        }
        # Skip completely blank rows
        if not any(normalized.values()):
            continue
        rows.append(normalized)

    if not rows:
        errors.append(RowError(0, "file", "CSV has a header but no data rows."))
    return headers, rows, errors


def _validate_email(value: str, row_num: int, errors: list[RowError]) -> None:
    if value and not EMAIL_RE.match(value):
        errors.append(RowError(row_num, "email", f"Invalid email address: {value}"))


def _validate_length(
    value: str,
    field_name: str,
    max_len: int,
    row_num: int,
    errors: list[RowError],
) -> None:
    if value and len(value) > max_len:
        errors.append(
            RowError(
                row_num,
                field_name,
                f"{field_name} exceeds {max_len} characters ({len(value)}).",
            )
        )


def _require_headers(headers: list[str], required: Iterable[str], errors: list[RowError]) -> None:
    missing = [col for col in required if col not in headers]
    if missing:
        errors.append(
            RowError(
                0,
                "headers",
                "Missing required column(s): " + ", ".join(missing),
            )
        )


def validate_leads_csv(file_storage: FileStorage) -> ValidationResult:
    headers, rows, errors = _read_csv_file(file_storage)
    if errors:
        return ValidationResult(valid=False, errors=errors, rows=[], headers=headers)

    _require_headers(headers, ["name"], errors)
    unknown = [h for h in headers if h not in LEAD_FIELDNAMES]
    if unknown:
        errors.append(
            RowError(
                0,
                "headers",
                "Unknown column(s): "
                + ", ".join(unknown)
                + f". Expected: {', '.join(LEAD_FIELDNAMES)}",
            )
        )

    users_by_username = {
        u.username.lower(): u for u in User.query.filter_by(is_active=True).all()
    }
    parsed: list[dict[str, Any]] = []

    for offset, row in enumerate(rows):
        row_num = offset + 2
        name = _cell(row, "name")
        if not name:
            errors.append(RowError(row_num, "name", "Name is required."))
        _validate_length(name, "name", 150, row_num, errors)

        email = _cell(row, "email")
        _validate_email(email, row_num, errors)
        _validate_length(email, "email", 120, row_num, errors)

        company = _cell(row, "company")
        phone = _cell(row, "phone")
        country = _cell(row, "country")
        industry = _cell(row, "industry")
        notes = _cell(row, "notes")
        _validate_length(company, "company", 150, row_num, errors)
        _validate_length(phone, "phone", 40, row_num, errors)
        _validate_length(country, "country", 100, row_num, errors)
        _validate_length(industry, "industry", 100, row_num, errors)

        source_raw = _cell(row, "lead_source") or "Website"
        source = LEAD_SOURCE_SET.get(source_raw.lower())
        if source is None:
            errors.append(
                RowError(
                    row_num,
                    "lead_source",
                    f"Invalid lead_source “{source_raw}”. "
                    f"Allowed: {', '.join(LEAD_SOURCES)}",
                )
            )

        status_raw = _cell(row, "status") or "New"
        status = LEAD_STATUS_SET.get(status_raw.lower())
        if status is None:
            errors.append(
                RowError(
                    row_num,
                    "status",
                    f"Invalid status “{status_raw}”. Allowed: {', '.join(LEAD_STATUSES)}",
                )
            )

        assigned_raw = _cell(row, "assigned_to")
        assigned_to_id = None
        if assigned_raw:
            user = users_by_username.get(assigned_raw.lower())
            if user is None:
                errors.append(
                    RowError(
                        row_num,
                        "assigned_to",
                        f"Unknown or inactive username: {assigned_raw}",
                    )
                )
            else:
                assigned_to_id = user.id

        parsed.append(
            {
                "name": name,
                "company": company or None,
                "email": email.lower() if email else None,
                "phone": phone or None,
                "country": country or None,
                "industry": industry or None,
                "lead_source": source or "Website",
                "status": status or "New",
                "notes": notes or None,
                "assigned_to_id": assigned_to_id,
            }
        )

    return ValidationResult(
        valid=not errors,
        errors=errors,
        rows=parsed if not errors else [],
        headers=headers,
    )


def validate_customers_csv(file_storage: FileStorage) -> ValidationResult:
    headers, rows, errors = _read_csv_file(file_storage)
    if errors:
        return ValidationResult(valid=False, errors=errors, rows=[], headers=headers)

    _require_headers(headers, ["name"], errors)
    unknown = [h for h in headers if h not in CUSTOMER_FIELDNAMES]
    if unknown:
        errors.append(
            RowError(
                0,
                "headers",
                "Unknown column(s): "
                + ", ".join(unknown)
                + f". Expected: {', '.join(CUSTOMER_FIELDNAMES)}",
            )
        )

    parsed: list[dict[str, Any]] = []
    for offset, row in enumerate(rows):
        row_num = offset + 2
        name = _cell(row, "name")
        if not name:
            errors.append(RowError(row_num, "name", "Name is required."))
        _validate_length(name, "name", 150, row_num, errors)

        email = _cell(row, "email")
        _validate_email(email, row_num, errors)
        _validate_length(email, "email", 120, row_num, errors)

        phone = _cell(row, "phone")
        address = _cell(row, "address")
        gst = _cell(row, "gst")
        website = _cell(row, "website")
        industry = _cell(row, "industry")
        primary_contact = _cell(row, "primary_contact")
        country = _cell(row, "country")
        notes = _cell(row, "notes")
        status_raw = _cell(row, "status") or "Active"

        _validate_length(phone, "phone", 40, row_num, errors)
        _validate_length(address, "address", 255, row_num, errors)
        _validate_length(gst, "gst", 40, row_num, errors)
        _validate_length(website, "website", 200, row_num, errors)
        _validate_length(industry, "industry", 100, row_num, errors)
        _validate_length(primary_contact, "primary_contact", 150, row_num, errors)
        _validate_length(country, "country", 100, row_num, errors)

        status_match = next(
            (s for s in CUSTOMER_STATUSES if s.lower() == status_raw.lower()),
            None,
        )
        if status_match is None:
            errors.append(
                RowError(
                    row_num,
                    "status",
                    f"Invalid status “{status_raw}”. Allowed: Active, Inactive",
                )
            )

        parsed.append(
            {
                "name": name,
                "email": email.lower() if email else None,
                "phone": phone or None,
                "address": address or None,
                "gst": gst or None,
                "website": website or None,
                "industry": industry or None,
                "primary_contact": primary_contact or None,
                "country": country or None,
                "status": status_match or "Active",
                "notes": notes or None,
            }
        )

    return ValidationResult(
        valid=not errors,
        errors=errors,
        rows=parsed if not errors else [],
        headers=headers,
    )


def import_leads(rows: list[dict[str, Any]], *, user_id: int | None = None) -> int:
    uid = user_id or current_user.id
    created = 0
    for data in rows:
        lead = Lead(
            name=data["name"],
            company=data.get("company"),
            email=data.get("email"),
            phone=data.get("phone"),
            country=data.get("country"),
            industry=data.get("industry"),
            lead_source=data.get("lead_source") or "Website",
            status=data.get("status") or "New",
            notes=data.get("notes"),
            assigned_to_id=data.get("assigned_to_id"),
            created_by_id=uid,
        )
        db.session.add(lead)
        created += 1
    db.session.flush()
    log_activity(
        "imported",
        f"Imported {created} lead(s) from CSV",
        entity_type="lead",
        details=f"count={created}",
        user_id=uid,
    )
    db.session.commit()
    return created


def import_customers(rows: list[dict[str, Any]], *, user_id: int | None = None) -> int:
    uid = user_id or current_user.id
    created = 0
    for data in rows:
        customer = Customer(
            name=data["name"],
            email=data.get("email"),
            phone=data.get("phone"),
            address=data.get("address"),
            gst=data.get("gst"),
            website=data.get("website"),
            industry=data.get("industry"),
            primary_contact=data.get("primary_contact"),
            country=data.get("country"),
            status=data.get("status") or "Active",
            notes=data.get("notes"),
            owner_id=uid,
        )
        db.session.add(customer)
        created += 1
    db.session.flush()
    log_activity(
        "imported",
        f"Imported {created} customer(s) from CSV",
        entity_type="customer",
        details=f"count={created}",
        user_id=uid,
    )
    db.session.commit()
    return created


def export_leads_csv(leads: Iterable[Lead] | None = None) -> str:
    if leads is None:
        from sqlalchemy.orm import joinedload

        query = (
            Lead.query.options(joinedload(Lead.assigned_employee))
            .order_by(Lead.created_at.desc())
            .all()
        )
    else:
        query = leads
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=LEAD_FIELDNAMES)
    writer.writeheader()
    for lead in query:
        writer.writerow(
            {
                "name": lead.name or "",
                "company": lead.company or "",
                "email": lead.email or "",
                "phone": lead.phone or "",
                "country": lead.country or "",
                "industry": lead.industry or "",
                "lead_source": lead.lead_source or "",
                "status": lead.status or "",
                "notes": (lead.notes or "").replace("\r\n", " ").replace("\n", " "),
                "assigned_to": (
                    lead.assigned_employee.username if lead.assigned_employee else ""
                ),
            }
        )
    return output.getvalue()


def export_customers_csv(customers: Iterable[Customer] | None = None) -> str:
    query = (
        customers
        if customers is not None
        else Customer.query.order_by(Customer.created_at.desc()).all()
    )
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CUSTOMER_FIELDNAMES)
    writer.writeheader()
    for customer in query:
        writer.writerow(
            {
                "name": customer.name or "",
                "email": customer.email or "",
                "phone": customer.phone or "",
                "address": customer.address or "",
                "gst": customer.gst or "",
                "website": customer.website or "",
                "industry": customer.industry or "",
                "primary_contact": customer.primary_contact or "",
                "country": customer.country or "",
                "status": customer.status or "",
                "notes": (customer.notes or "").replace("\r\n", " ").replace("\n", " "),
            }
        )
    return output.getvalue()


def sample_leads_csv() -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=LEAD_FIELDNAMES)
    writer.writeheader()
    writer.writerow(
        {
            "name": "Jane Prospect",
            "company": "Orbit Labs",
            "email": "jane@example.com",
            "phone": "+1-555-0100",
            "country": "USA",
            "industry": "Technology",
            "lead_source": "Website",
            "status": "New",
            "notes": "Interested in demo",
            "assigned_to": "employee",
        }
    )
    return output.getvalue()


def sample_customers_csv() -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CUSTOMER_FIELDNAMES)
    writer.writeheader()
    writer.writerow(
        {
            "name": "Orbit Labs",
            "email": "billing@example.com",
            "phone": "+1-555-0101",
            "address": "100 Market St",
            "gst": "GST123",
            "website": "https://example.com",
            "industry": "Technology",
            "primary_contact": "Jane Prospect",
            "country": "USA",
            "status": "Active",
            "notes": "Imported sample",
        }
    )
    return output.getvalue()
