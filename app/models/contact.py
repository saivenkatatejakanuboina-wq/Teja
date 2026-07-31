"""Contact model."""

from datetime import datetime, timezone

from app.extensions import db


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
