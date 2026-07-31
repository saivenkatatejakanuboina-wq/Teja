"""SQLAlchemy models for the Mini CRM (MVC Model layer)."""

import json
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_EMPLOYEE = "employee"
USER_ROLES = (ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE)

PERMISSIONS = (
    ("manage_users", "Manage Users"),
    ("manage_settings", "Manage Settings"),
    ("manage_leads", "Manage Leads"),
    ("manage_customers", "Manage Customers"),
    ("manage_deals", "Manage Deals"),
    ("manage_followups", "Manage Follow-ups"),
    ("manage_tasks", "Manage Tasks"),
    ("view_reports", "View Reports"),
)

DEFAULT_ROLE_PERMISSIONS = {
    ROLE_ADMIN: [key for key, _ in PERMISSIONS],
    ROLE_MANAGER: [
        "manage_leads",
        "manage_customers",
        "manage_deals",
        "manage_followups",
        "manage_tasks",
        "view_reports",
    ],
    ROLE_EMPLOYEE: [
        "manage_leads",
        "manage_customers",
        "manage_followups",
        "manage_tasks",
    ],
}

DEAL_STAGES = (
    "Prospecting",
    "Qualification",
    "Proposal",
    "Negotiation",
    "Closed Won",
    "Closed Lost",
)

LEAD_STATUSES = (
    "New",
    "Contacted",
    "Qualified",
    "Proposal",
    "Negotiation",
    "Won",
    "Lost",
)

LEAD_SOURCES = (
    "Website",
    "Referral",
    "Cold Call",
    "Social Media",
    "Email Campaign",
    "Trade Show",
    "Advertisement",
    "Other",
)

FOLLOWUP_TYPES = (
    "Call",
    "Meeting",
    "WhatsApp",
    "Email",
)

FOLLOWUP_STATUSES = (
    "Scheduled",
    "Completed",
    "Missed",
    "Cancelled",
)

TASK_PRIORITIES = (
    "Low",
    "Medium",
    "High",
    "Urgent",
)

TASK_STATUSES = (
    "To Do",
    "In Progress",
    "Completed",
    "On Hold",
    "Cancelled",
)

THEME_OPTIONS = (
    "light",
    "dark",
    "ocean",
)

CURRENCY_OPTIONS = (
    ("USD", "USD — US Dollar"),
    ("EUR", "EUR — Euro"),
    ("GBP", "GBP — British Pound"),
    ("INR", "INR — Indian Rupee"),
    ("AED", "AED — UAE Dirham"),
    ("AUD", "AUD — Australian Dollar"),
)

TIMEZONE_OPTIONS = (
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Berlin",
    "Asia/Kolkata",
    "Asia/Dubai",
    "Asia/Singapore",
    "Australia/Sydney",
)


class User(UserMixin, db.Model):
    """Authenticated user with role-based permissions."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default=ROLE_EMPLOYEE, nullable=False, index=True)
    permissions_json = db.Column(db.Text, default="[]")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    contacts = db.relationship("Contact", back_populates="owner", lazy="dynamic")
    companies = db.relationship("Company", back_populates="owner", lazy="dynamic")
    deals = db.relationship("Deal", back_populates="owner", lazy="dynamic")
    customers = db.relationship("Customer", back_populates="owner", lazy="dynamic")
    followups = db.relationship(
        "FollowUp",
        back_populates="assigned_to",
        foreign_keys="FollowUp.assigned_to_id",
        lazy="dynamic",
    )
    created_followups = db.relationship(
        "FollowUp",
        back_populates="created_by",
        foreign_keys="FollowUp.created_by_id",
        lazy="dynamic",
    )
    assigned_tasks = db.relationship(
        "Task",
        back_populates="assigned_to",
        foreign_keys="Task.assigned_to_id",
        lazy="dynamic",
    )
    created_tasks = db.relationship(
        "Task",
        back_populates="created_by",
        foreign_keys="Task.created_by_id",
        lazy="dynamic",
    )
    created_leads = db.relationship(
        "Lead",
        back_populates="created_by",
        foreign_keys="Lead.created_by_id",
        lazy="dynamic",
    )
    assigned_leads = db.relationship(
        "Lead",
        back_populates="assigned_employee",
        foreign_keys="Lead.assigned_to_id",
        lazy="dynamic",
    )
    activities = db.relationship("ActivityLog", back_populates="user", lazy="dynamic")
    login_history = db.relationship(
        "LoginHistory",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def is_manager(self) -> bool:
        return self.role == ROLE_MANAGER

    @property
    def is_employee(self) -> bool:
        return self.role == ROLE_EMPLOYEE

    @property
    def role_label(self) -> str:
        return {
            ROLE_ADMIN: "Admin",
            ROLE_MANAGER: "Manager",
            ROLE_EMPLOYEE: "Employee",
        }.get(self.role, self.role.title())

    def get_permissions(self) -> list[str]:
        if self.is_admin:
            return [key for key, _ in PERMISSIONS]
        raw = self.permissions_json or "[]"
        try:
            data = json.loads(raw)
            if isinstance(data, list) and data:
                return data
        except json.JSONDecodeError:
            pass
        return list(DEFAULT_ROLE_PERMISSIONS.get(self.role, []))

    def set_permissions(self, permissions: list[str]) -> None:
        valid = {key for key, _ in PERMISSIONS}
        cleaned = [p for p in permissions if p in valid]
        self.permissions_json = json.dumps(cleaned)

    def has_permission(self, permission: str) -> bool:
        if self.is_admin:
            return True
        return permission in self.get_permissions()

    def apply_role_defaults(self) -> None:
        self.set_permissions(DEFAULT_ROLE_PERMISSIONS.get(self.role, []))

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


class LoginHistory(db.Model):
    """Record of user login attempts."""

    __tablename__ = "login_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    username_attempted = db.Column(db.String(80), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="success", index=True)
    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    user = db.relationship("User", back_populates="login_history")

    def __repr__(self) -> str:
        return f"<LoginHistory {self.username_attempted} {self.status}>"


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    industry = db.Column(db.String(100))
    website = db.Column(db.String(200))
    phone = db.Column(db.String(40))
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    notes = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner = db.relationship("User", back_populates="companies")
    contacts = db.relationship("Contact", back_populates="company", lazy="dynamic")
    deals = db.relationship("Deal", back_populates="company", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Company {self.name}>"


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(40))
    job_title = db.Column(db.String(120))
    status = db.Column(db.String(40), default="Lead", nullable=False)
    notes = db.Column(db.Text)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner = db.relationship("User", back_populates="contacts")
    company = db.relationship("Company", back_populates="contacts")
    deals = db.relationship("Deal", back_populates="contact", lazy="dynamic")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Contact {self.full_name}>"


class Deal(db.Model):
    __tablename__ = "deals"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    value = db.Column(db.Float, default=0.0, nullable=False)
    stage = db.Column(db.String(40), default="Prospecting", nullable=False)
    probability = db.Column(db.Integer, default=10, nullable=False)
    expected_close_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner = db.relationship("User", back_populates="deals")
    company = db.relationship("Company", back_populates="deals")
    contact = db.relationship("Contact", back_populates="deals")

    @property
    def weighted_value(self) -> float:
        return round((self.value or 0) * (self.probability or 0) / 100, 2)

    def __repr__(self) -> str:
        return f"<Deal {self.title}>"


class Lead(db.Model):
    """Sales lead record for the Lead Management module."""

    __tablename__ = "leads"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    company = db.Column(db.String(150), index=True)
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(40))
    country = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    lead_source = db.Column(db.String(60), default="Website", nullable=False)
    status = db.Column(db.String(40), default="New", nullable=False, index=True)
    notes = db.Column(db.Text)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    assigned_employee = db.relationship(
        "User",
        foreign_keys=[assigned_to_id],
        back_populates="assigned_leads",
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="created_leads",
    )
    activities = db.relationship(
        "ActivityLog",
        back_populates="lead",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    customer = db.relationship(
        "Customer",
        back_populates="source_lead",
        uselist=False,
    )

    @property
    def is_converted(self) -> bool:
        return self.customer is not None

    def __repr__(self) -> str:
        return f"<Lead {self.name}>"


class Customer(db.Model):
    """Customer record — created directly or converted from a Lead."""

    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(40))
    address = db.Column(db.String(255))
    gst = db.Column(db.String(40), index=True)
    website = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    primary_contact = db.Column(db.String(150))
    notes = db.Column(db.Text)
    status = db.Column(db.String(40), default="Active", nullable=False, index=True)
    country = db.Column(db.String(100))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), unique=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner = db.relationship("User", back_populates="customers")
    source_lead = db.relationship(
        "Lead",
        back_populates="customer",
        foreign_keys=[lead_id],
    )

    def __repr__(self) -> str:
        return f"<Customer {self.name}>"


class FollowUp(db.Model):
    """Scheduled follow-up (call, meeting, WhatsApp, email)."""

    __tablename__ = "followups"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    followup_type = db.Column(db.String(40), nullable=False, default="Call", index=True)
    reminder_date = db.Column(db.Date, nullable=False, index=True)
    reminder_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(40), default="Scheduled", nullable=False, index=True)
    remarks = db.Column(db.Text)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"))
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    lead = db.relationship("Lead", backref=db.backref("followups", lazy="dynamic"))
    customer = db.relationship("Customer", backref=db.backref("followups", lazy="dynamic"))
    assigned_to = db.relationship(
        "User",
        foreign_keys=[assigned_to_id],
        back_populates="followups",
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="created_followups",
    )

    @property
    def reminder_datetime(self) -> datetime:
        return datetime.combine(self.reminder_date, self.reminder_time)

    @property
    def is_overdue(self) -> bool:
        if self.status in ("Completed", "Cancelled"):
            return False
        return self.reminder_datetime < datetime.now()

    @property
    def effective_status(self) -> str:
        if self.status == "Scheduled" and self.is_overdue:
            return "Missed"
        return self.status

    @property
    def related_name(self) -> str:
        if self.customer:
            return self.customer.name
        if self.lead:
            return self.lead.name
        return "—"

    def __repr__(self) -> str:
        return f"<FollowUp {self.title}>"


class Task(db.Model):
    """Assignable work item with priority, status, and due dates."""

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default="Medium", nullable=False, index=True)
    status = db.Column(db.String(40), default="To Do", nullable=False, index=True)
    due_date = db.Column(db.Date, index=True)
    completed_date = db.Column(db.Date)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    assigned_to = db.relationship(
        "User",
        foreign_keys=[assigned_to_id],
        back_populates="assigned_tasks",
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="created_tasks",
    )

    @property
    def is_overdue(self) -> bool:
        if self.status in ("Completed", "Cancelled") or self.due_date is None:
            return False
        from datetime import date

        return self.due_date < date.today()

    @property
    def priority_slug(self) -> str:
        return self.priority.lower().replace(" ", "-")

    @property
    def status_slug(self) -> str:
        return self.status.lower().replace(" ", "-")

    def __repr__(self) -> str:
        return f"<Task {self.title}>"


class ActivityLog(db.Model):
    """Audit trail for lead/customer (and related) actions."""

    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(40), nullable=False, index=True)
    entity_type = db.Column(db.String(40), default="lead", nullable=False)
    entity_id = db.Column(db.Integer)
    message = db.Column(db.String(500), nullable=False)
    details = db.Column(db.Text)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id", ondelete="CASCADE"))
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    lead = db.relationship("Lead", back_populates="activities")
    customer = db.relationship("Customer", backref=db.backref("activities", lazy="dynamic"))
    user = db.relationship("User", back_populates="activities")

    def __repr__(self) -> str:
        return f"<ActivityLog {self.action} #{self.id}>"


class AppSettings(db.Model):
    """Singleton application settings (company, SMTP, theme, etc.)."""

    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), default="Mini CRM", nullable=False)
    logo_filename = db.Column(db.String(255))
    timezone = db.Column(db.String(80), default="UTC", nullable=False)
    currency = db.Column(db.String(10), default="USD", nullable=False)
    theme = db.Column(db.String(20), default="light", nullable=False)

    smtp_host = db.Column(db.String(150))
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(150))
    smtp_password = db.Column(db.String(255))
    smtp_use_tls = db.Column(db.Boolean, default=True, nullable=False)
    smtp_from_email = db.Column(db.String(150))

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AppSettings {self.company_name}>"
