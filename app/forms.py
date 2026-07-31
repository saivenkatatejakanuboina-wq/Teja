"""WTForms for the Mini CRM — includes auth form validation."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateField,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
)
from wtforms.widgets import CheckboxInput, ListWidget
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

from app.models import (
    CURRENCY_OPTIONS,
    DEAL_STAGES,
    FOLLOWUP_STATUSES,
    FOLLOWUP_TYPES,
    LEAD_SOURCES,
    LEAD_STATUSES,
    PERMISSIONS,
    TASK_PRIORITIES,
    TASK_STATUSES,
    THEME_OPTIONS,
    TIMEZONE_OPTIONS,
    USER_ROLES,
    User,
)


class MultiCheckboxField(SelectMultipleField):
    """Render a SelectMultipleField as a list of checkboxes."""

    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

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


CUSTOMER_STATUSES = [
    ("Active", "Active"),
    ("Inactive", "Inactive"),
]


class CustomerForm(FlaskForm):
    name = StringField(
        "Customer Name",
        validators=[
            DataRequired(message="Customer name is required."),
            Length(max=150),
        ],
    )
    primary_contact = StringField(
        "Primary Contact",
        validators=[Optional(), Length(max=150)],
    )
    email = StringField(
        "Email",
        validators=[
            Optional(),
            Email(message="Enter a valid email address."),
            Length(max=120),
        ],
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    gst = StringField(
        "GST",
        validators=[Optional(), Length(max=40)],
    )
    website = StringField("Website", validators=[Optional(), Length(max=200)])
    industry = StringField("Industry", validators=[Optional(), Length(max=100)])
    country = StringField("Country", validators=[Optional(), Length(max=100)])
    status = SelectField(
        "Status",
        choices=CUSTOMER_STATUSES,
        validators=[DataRequired()],
        default="Active",
    )
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=5000)])
    submit = SubmitField("Save Customer")


class LeadForm(FlaskForm):
    name = StringField(
        "Lead Name",
        validators=[
            DataRequired(message="Lead name is required."),
            Length(max=150),
        ],
    )
    company = StringField("Company", validators=[Optional(), Length(max=150)])
    email = StringField(
        "Email",
        validators=[
            Optional(),
            Email(message="Enter a valid email address."),
            Length(max=120),
        ],
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    country = StringField("Country", validators=[Optional(), Length(max=100)])
    industry = StringField("Industry", validators=[Optional(), Length(max=100)])
    lead_source = SelectField(
        "Lead Source",
        choices=[(s, s) for s in LEAD_SOURCES],
        validators=[DataRequired(message="Lead source is required.")],
    )
    status = SelectField(
        "Status",
        choices=[(s, s) for s in LEAD_STATUSES],
        validators=[DataRequired(message="Status is required.")],
    )
    assigned_to_id = SelectField(
        "Assigned Employee",
        coerce=int,
        validators=[Optional()],
    )
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=5000)])
    submit = SubmitField("Save Lead")


class FollowUpForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(max=150),
        ],
    )
    followup_type = SelectField(
        "Type",
        choices=[(t, t) for t in FOLLOWUP_TYPES],
        validators=[DataRequired(message="Follow-up type is required.")],
    )
    reminder_date = DateField(
        "Reminder Date",
        validators=[DataRequired(message="Reminder date is required.")],
        format="%Y-%m-%d",
    )
    reminder_time = TimeField(
        "Reminder Time",
        validators=[DataRequired(message="Reminder time is required.")],
        format="%H:%M",
    )
    status = SelectField(
        "Status",
        choices=[(s, s) for s in FOLLOWUP_STATUSES],
        validators=[DataRequired()],
        default="Scheduled",
    )
    assigned_to_id = SelectField(
        "Assigned Employee",
        coerce=int,
        validators=[DataRequired(message="Please assign an employee.")],
    )
    lead_id = SelectField("Related Lead", coerce=int, validators=[Optional()])
    customer_id = SelectField("Related Customer", coerce=int, validators=[Optional()])
    remarks = TextAreaField("Remarks", validators=[Optional(), Length(max=5000)])
    submit = SubmitField("Save Follow-up")


class TaskForm(FlaskForm):
    title = StringField(
        "Task Title",
        validators=[
            DataRequired(message="Task title is required."),
            Length(max=150),
        ],
    )
    description = TextAreaField("Description", validators=[Optional(), Length(max=5000)])
    assigned_to_id = SelectField(
        "Assign Employee",
        coerce=int,
        validators=[DataRequired(message="Please assign an employee.")],
    )
    priority = SelectField(
        "Priority",
        choices=[(p, p) for p in TASK_PRIORITIES],
        validators=[DataRequired()],
        default="Medium",
    )
    status = SelectField(
        "Status",
        choices=[(s, s) for s in TASK_STATUSES],
        validators=[DataRequired()],
        default="To Do",
    )
    due_date = DateField(
        "Due Date",
        validators=[Optional()],
        format="%Y-%m-%d",
    )
    completed_date = DateField(
        "Completed Date",
        validators=[Optional()],
        format="%Y-%m-%d",
    )
    submit = SubmitField("Save Task")


class CompanySettingsForm(FlaskForm):
    company_name = StringField(
        "Company Name",
        validators=[DataRequired(message="Company name is required."), Length(max=150)],
    )
    logo = FileField(
        "Company Logo",
        validators=[
            Optional(),
            FileAllowed(
                ["png", "jpg", "jpeg", "gif", "webp", "svg"],
                "Images only (png, jpg, gif, webp, svg).",
            ),
        ],
    )
    timezone = SelectField(
        "Timezone",
        choices=[(tz, tz) for tz in TIMEZONE_OPTIONS],
        validators=[DataRequired()],
    )
    currency = SelectField(
        "Currency",
        choices=list(CURRENCY_OPTIONS),
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Company Settings")


class SMTPSettingsForm(FlaskForm):
    smtp_host = StringField("SMTP Host", validators=[Optional(), Length(max=150)])
    smtp_port = IntegerField(
        "SMTP Port",
        validators=[Optional(), NumberRange(min=1, max=65535)],
        default=587,
    )
    smtp_username = StringField("SMTP Username", validators=[Optional(), Length(max=150)])
    smtp_password = PasswordField("SMTP Password", validators=[Optional(), Length(max=255)])
    smtp_from_email = StringField(
        "From Email",
        validators=[Optional(), Email(), Length(max=150)],
    )
    smtp_use_tls = BooleanField("Use TLS", default=True)
    submit = SubmitField("Save SMTP Settings")


class ThemeSettingsForm(FlaskForm):
    theme = SelectField(
        "Theme",
        choices=[(t, t.title()) for t in THEME_OPTIONS],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Theme")


class ProfileForm(FlaskForm):
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(message="Full name is required."), Length(max=120)],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Enter a valid email address."),
            Length(max=120),
        ],
    )
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username is required."),
            Length(min=3, max=80),
        ],
    )
    submit = SubmitField("Update Profile")

    def __init__(self, original_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_user = original_user

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data.strip()).first()
        if user and (self.original_user is None or user.id != self.original_user.id):
            raise ValidationError("Username is already taken.")

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data.strip().lower()).first()
        if user and (self.original_user is None or user.id != self.original_user.id):
            raise ValidationError("Email is already registered.")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired(message="Current password is required.")],
    )
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="New password is required."),
            Length(min=6, message="Password must be at least 6 characters."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(message="Please confirm the new password."),
            EqualTo("new_password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Change Password")


class RestoreDatabaseForm(FlaskForm):
    backup_file = FileField(
        "Backup File (.db)",
        validators=[
            DataRequired(message="Please choose a database backup file."),
            FileAllowed(["db", "sqlite"], "SQLite database files only (.db)."),
        ],
    )
    submit = SubmitField("Restore Database")


class AdminUserForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username is required."),
            Length(min=3, max=80),
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
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(message="Full name is required."), Length(max=120)],
    )
    role = SelectField(
        "Role",
        choices=[(r, r.title()) for r in USER_ROLES],
        validators=[DataRequired()],
    )
    is_active = BooleanField("Active", default=True)
    password = PasswordField(
        "Password",
        validators=[Optional(), Length(min=6, max=128)],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            Optional(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    permissions = MultiCheckboxField(
        "Permissions",
        choices=[(key, label) for key, label in PERMISSIONS],
        validators=[Optional()],
    )
    submit = SubmitField("Save User")

    def __init__(self, original_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_user = original_user

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data.strip()).first()
        if user and (self.original_user is None or user.id != self.original_user.id):
            raise ValidationError("Username is already taken.")

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data.strip().lower()).first()
        if user and (self.original_user is None or user.id != self.original_user.id):
            raise ValidationError("Email is already registered.")


class AdminResetPasswordForm(FlaskForm):
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="New password is required."),
            Length(min=6, message="Password must be at least 6 characters."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm the password."),
            EqualTo("new_password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Reset Password")


class CSVImportForm(FlaskForm):
    csv_file = FileField(
        "CSV File",
        validators=[
            DataRequired(message="Please choose a CSV file."),
            FileAllowed(["csv"], "CSV files only (.csv)."),
        ],
    )
    submit = SubmitField("Validate & Import")
