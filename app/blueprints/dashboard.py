"""Dashboard blueprint — professional CRM overview with dummy demo data."""

from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import current_user, login_required

dashboard_bp = Blueprint("dashboard", __name__)


def _dummy_dashboard_data():
    """Return demo KPI, chart, and activity data for the CRM dashboard."""
    today = datetime.utcnow().date()

    cards = {
        "total_leads": 248,
        "todays_leads": 14,
        "customers": 86,
        "followups_today": 9,
        "won_deals": 32,
        "lost_deals": 11,
    }

    # Lead trend for the last 7 days (line chart)
    lead_trend = {
        "labels": [
            (today - timedelta(days=i)).strftime("%a")
            for i in range(6, -1, -1)
        ],
        "values": [18, 22, 15, 28, 24, 19, 14],
    }

    # Deal outcomes (doughnut)
    deal_outcomes = {
        "labels": ["Won Deals", "Lost Deals", "Open Pipeline"],
        "values": [32, 11, 47],
    }

    # Pipeline by stage (bar)
    pipeline_stages = {
        "labels": [
            "Prospecting",
            "Qualification",
            "Proposal",
            "Negotiation",
            "Closed Won",
            "Closed Lost",
        ],
        "values": [22, 18, 14, 11, 32, 11],
    }

    # Monthly revenue (bar)
    revenue_trend = {
        "labels": ["Feb", "Mar", "Apr", "May", "Jun", "Jul"],
        "won": [42000, 51000, 38500, 62000, 57400, 71000],
        "pipeline": [88000, 92000, 76500, 101000, 95000, 112000],
    }

    recent_activities = [
        {
            "icon": "bi-person-plus",
            "tone": "primary",
            "title": "New lead added",
            "detail": "Sarah Chen from NovaTech inquired about Enterprise plan",
            "time": "12 min ago",
        },
        {
            "icon": "bi-telephone",
            "tone": "info",
            "title": "Follow-up completed",
            "detail": "Called Marcus Lee — demo scheduled for tomorrow 10:00 AM",
            "time": "35 min ago",
        },
        {
            "icon": "bi-trophy",
            "tone": "success",
            "title": "Deal won",
            "detail": "Closed “Cloud Migration” with Apex Systems — $48,000",
            "time": "1 hour ago",
        },
        {
            "icon": "bi-envelope",
            "tone": "warning",
            "title": "Proposal sent",
            "detail": "Sent pricing proposal to GreenLeaf Retail",
            "time": "2 hours ago",
        },
        {
            "icon": "bi-x-circle",
            "tone": "danger",
            "title": "Deal lost",
            "detail": "“Support Retainer” with Orion Media marked Closed Lost",
            "time": "3 hours ago",
        },
        {
            "icon": "bi-building",
            "tone": "secondary",
            "title": "Company updated",
            "detail": "Updated industry and website for BrightPath Logistics",
            "time": "Yesterday",
        },
        {
            "icon": "bi-calendar-check",
            "tone": "primary",
            "title": "Follow-up due today",
            "detail": "9 follow-ups scheduled — 4 remaining",
            "time": "Today",
        },
    ]

    top_deals = [
        {"title": "Enterprise Rollout", "company": "NovaTech", "value": 72000, "stage": "Negotiation"},
        {"title": "Cloud Migration", "company": "Apex Systems", "value": 48000, "stage": "Closed Won"},
        {"title": "Annual Support", "company": "GreenLeaf Retail", "value": 26500, "stage": "Proposal"},
        {"title": "Pilot License", "company": "BrightPath Logistics", "value": 15000, "stage": "Qualification"},
        {"title": "Support Retainer", "company": "Orion Media", "value": 9800, "stage": "Closed Lost"},
    ]

    return {
        "cards": cards,
        "lead_trend": lead_trend,
        "deal_outcomes": deal_outcomes,
        "pipeline_stages": pipeline_stages,
        "revenue_trend": revenue_trend,
        "recent_activities": recent_activities,
        "top_deals": top_deals,
        "is_dummy": True,
    }


@dashboard_bp.route("/")
@login_required
def index():
    data = _dummy_dashboard_data()
    return render_template(
        "dashboard/index.html",
        title="Dashboard",
        user=current_user,
        **data,
    )
