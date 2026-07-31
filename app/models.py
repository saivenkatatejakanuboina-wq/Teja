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
