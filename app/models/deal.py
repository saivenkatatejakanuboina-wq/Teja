"""Deal / opportunity model."""

from datetime import datetime, timezone

from app.extensions import db


DEAL_STAGES = (
    "Prospecting",
    "Qualification",
    "Proposal",
    "Negotiation",
    "Closed Won",
    "Closed Lost",
)


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
