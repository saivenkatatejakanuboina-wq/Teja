"""WTForms for the Mini CRM — includes auth form validation."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

from app.models import DEAL_STAGES, User

CONTACT_STATUSES = [
    ("Lead", "Lead"),
    ("Prospect", "Prospect"),
    ("Customer", "Customer"),
    ("Inactive", "Inactive"),
]


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(message="Username is required."), Length(max=80)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required.")],
    )
    remember_me = BooleanField("Remember me", default=False)
    submit = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(message="Full name is required."), Length(max=120)],
    )
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username is required."),
            Length(min=3, max=80, message="Username must be 3–80 characters."),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Enter a valid email address."),
            Length(max=120),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=6, message="Password must be at least 6 characters."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Create Employee Account")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError("Username is already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("Email is already registered.")


class CompanyForm(FlaskForm):
    name = StringField("Company Name", validators=[DataRequired(), Length(max=150)])
    industry = StringField("Industry", validators=[Optional(), Length(max=100)])
    website = StringField("Website", validators=[Optional(), Length(max=200)])
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    city = StringField("City", validators=[Optional(), Length(max=100)])
    country = StringField("Country", validators=[Optional(), Length(max=100)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Save Company")


class ContactForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=80)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    job_title = StringField("Job Title", validators=[Optional(), Length(max=120)])
    status = SelectField("Status", choices=CONTACT_STATUSES, validators=[DataRequired()])
    company_id = SelectField("Company", coerce=int, validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Save Contact")


class DealForm(FlaskForm):
    title = StringField("Deal Title", validators=[DataRequired(), Length(max=150)])
    value = FloatField("Value ($)", validators=[DataRequired(), NumberRange(min=0)])
    stage = SelectField(
        "Stage",
        choices=[(s, s) for s in DEAL_STAGES],
        validators=[DataRequired()],
    )
    probability = IntegerField(
        "Probability (%)",
        validators=[DataRequired(), NumberRange(min=0, max=100)],
        default=10,
    )
    expected_close_date = DateField("Expected Close Date", validators=[Optional()])
    company_id = SelectField("Company", coerce=int, validators=[Optional()])
    contact_id = SelectField("Contact", coerce=int, validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Save Deal")
