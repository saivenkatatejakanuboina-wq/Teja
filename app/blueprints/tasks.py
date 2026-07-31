"""Task Management — create, assign, filter, and task dashboard."""

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.forms import TaskForm
from app.models import TASK_PRIORITIES, TASK_STATUSES, Task
from app.services.activity import log_activity
from app.services.choices import active_employees, employee_choices
from app.utils.db import get_or_404
from app.utils.pagination import paginate

tasks_bp = Blueprint("tasks", __name__)

PER_PAGE = 10


def _get_task_or_404(task_id: int) -> Task:
    return get_or_404(Task, task_id)


def _populate_form(form: TaskForm) -> None:
    form.assigned_to_id.choices = employee_choices(include_unassigned=False)


def _apply_form_data(task: Task, form: TaskForm) -> None:
    task.title = form.title.data.strip()
    task.description = form.description.data.strip() if form.description.data else None
    task.assigned_to_id = form.assigned_to_id.data
    task.priority = form.priority.data
    task.status = form.status.data
    task.due_date = form.due_date.data
    task.completed_date = form.completed_date.data

    if task.status == "Completed" and task.completed_date is None:
        task.completed_date = date.today()
    if task.status != "Completed":
        # Keep completed_date if manually set only when status is Completed
        if form.completed_date.data is None:
            task.completed_date = None


def _dashboard_stats() -> dict:
    today = date.today()
    total = Task.query.count()
    todo = Task.query.filter_by(status="To Do").count()
    in_progress = Task.query.filter_by(status="In Progress").count()
    completed = Task.query.filter_by(status="Completed").count()
    overdue = Task.query.filter(
        Task.due_date < today,
        Task.status.notin_(["Completed", "Cancelled"]),
    ).count()
    due_today = Task.query.filter(
        Task.due_date == today,
        Task.status.notin_(["Completed", "Cancelled"]),
    ).count()

    by_priority = {
        row[0]: row[1]
        for row in db.session.query(Task.priority, func.count(Task.id))
        .group_by(Task.priority)
        .all()
    }
    by_status = {
        row[0]: row[1]
        for row in db.session.query(Task.status, func.count(Task.id))
        .group_by(Task.status)
        .all()
    }

    recent = Task.query.order_by(Task.created_at.desc()).limit(5).all()
    my_open = (
        Task.query.filter(
            Task.assigned_to_id == current_user.id,
            Task.status.notin_(["Completed", "Cancelled"]),
        )
        .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total": total,
        "todo": todo,
        "in_progress": in_progress,
        "completed": completed,
        "overdue": overdue,
        "due_today": due_today,
        "by_priority": by_priority,
        "by_status": by_status,
        "recent": recent,
        "my_open": my_open,
    }


@tasks_bp.route("/")
@login_required
def index():
    """Task list with search and filters."""
    from sqlalchemy.orm import joinedload

    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()
    assigned = request.args.get("assigned", "").strip()
    due = request.args.get("due", "").strip()
    today = date.today()

    query = Task.query.options(joinedload(Task.assigned_to))
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Task.title.ilike(like), Task.description.ilike(like))
        )
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned.isdigit():
        query = query.filter(Task.assigned_to_id == int(assigned))
    if due == "today":
        query = query.filter(Task.due_date == today)
    elif due == "overdue":
        query = query.filter(
            Task.due_date < today,
            Task.status.notin_(["Completed", "Cancelled"]),
        )
    elif due == "upcoming":
        query = query.filter(Task.due_date > today)

    query = query.order_by(
        Task.due_date.asc().nullslast(),
        Task.created_at.desc(),
    )
    pagination = paginate(query, per_page=PER_PAGE)
    employees = active_employees()

    return render_template(
        "tasks/index.html",
        title="Tasks",
        tasks=pagination.items,
        pagination=pagination,
        q=q,
        status=status,
        priority=priority,
        assigned=assigned,
        due=due,
        statuses=TASK_STATUSES,
        priorities=TASK_PRIORITIES,
        employees=employees,
    )


@tasks_bp.route("/dashboard")
@login_required
def dashboard():
    """Task dashboard with summary cards and lists."""
    stats = _dashboard_stats()
    return render_template(
        "tasks/dashboard.html",
        title="Task Dashboard",
        priorities=TASK_PRIORITIES,
        statuses=TASK_STATUSES,
        **stats,
    )


@tasks_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = TaskForm()
    _populate_form(form)
    if request.method == "GET":
        form.assigned_to_id.data = current_user.id
        form.priority.data = "Medium"
        form.status.data = "To Do"

    if form.validate_on_submit():
        task = Task(created_by_id=current_user.id)
        _apply_form_data(task, form)
        db.session.add(task)
        db.session.flush()
        log_activity(
            "created",
            f"Created task “{task.title}”",
            entity_type="task",
            entity_id=task.id,
            details=f"Priority: {task.priority}; Status: {task.status}",
        )
        db.session.commit()
        flash("Task created successfully.", "success")
        return redirect(url_for("tasks.detail", task_id=task.id))

    return render_template("tasks/form.html", form=form, title="Create Task")


@tasks_bp.route("/<int:task_id>")
@login_required
def detail(task_id: int):
    task = _get_task_or_404(task_id)
    return render_template("tasks/detail.html", task=task, title=task.title)


@tasks_bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit(task_id: int):
    task = _get_task_or_404(task_id)
    form = TaskForm(obj=task)
    _populate_form(form)
    if request.method == "GET":
        form.assigned_to_id.data = task.assigned_to_id

    if form.validate_on_submit():
        _apply_form_data(task, form)
        log_activity(
            "updated",
            f"Updated task “{task.title}”",
            entity_type="task",
            entity_id=task.id,
            details=f"Priority: {task.priority}; Status: {task.status}",
        )
        db.session.commit()
        flash("Task updated successfully.", "success")
        return redirect(url_for("tasks.detail", task_id=task.id))

    return render_template(
        "tasks/form.html",
        form=form,
        title="Edit Task",
        task=task,
    )


@tasks_bp.route("/<int:task_id>/complete", methods=["POST"])
@login_required
def complete(task_id: int):
    task = _get_task_or_404(task_id)
    task.status = "Completed"
    task.completed_date = date.today()
    log_activity(
        "completed",
        f"Completed task “{task.title}”",
        entity_type="task",
        entity_id=task.id,
    )
    db.session.commit()
    flash("Task marked as completed.", "success")
    from app.utils.security import safe_referrer_or

    return redirect(safe_referrer_or(url_for("tasks.index")))


@tasks_bp.route("/<int:task_id>/delete", methods=["POST"])
@login_required
def delete(task_id: int):
    task = _get_task_or_404(task_id)
    title = task.title
    log_activity(
        "deleted",
        f"Deleted task “{title}”",
        entity_type="task",
        entity_id=task_id,
        details=f"Priority: {task.priority}; Status: {task.status}",
    )
    db.session.delete(task)
    db.session.commit()
    flash(f"Task “{title}” deleted.", "info")
    return redirect(url_for("tasks.index"))
