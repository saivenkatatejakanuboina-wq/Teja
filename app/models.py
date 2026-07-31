"""SQLAlchemy models for the Mini CRM (MVC Model layer)."""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

ROLE_ADMIN = "admin"
ROLE_EMPLOYEE = "employee"
USER_ROLES = (ROLE_ADMIN, ROLE_EMPLOYEE)

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


class User(UserMixin, db.Model):
    """Authenticated user with Admin or Employee role."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default=ROLE_EMPLOYEE, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    contacts = db.relationship("Contact", back_populates="owner", lazy="dynamic")
    companies = db.relationship("Company", back_populates="owner", lazy="dynamic")
    deals = db.relationship("Deal", back_populates="owner", lazy="dynamic")
    customers = db.relationship("Customer", back_populates="owner", lazy="dynamic")
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
    def is_employee(self) -> bool:
        return self.role == ROLE_EMPLOYEE

    @property
    def role_label(self) -> str:
        return "Admin" if self.is_admin else "Employee"

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


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
