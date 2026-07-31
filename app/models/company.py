"""Company model."""

from datetime import datetime, timezone

from app.extensions import db


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
