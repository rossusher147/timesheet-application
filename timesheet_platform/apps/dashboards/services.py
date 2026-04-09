from datetime import timedelta

from apps.notifications.models import Notification
from apps.timesheets.models import Timesheet
from apps.timesheets.services import current_week_start, get_business_now


def unread_notifications_for_user(user, limit=10):
    return Notification.objects.filter(recipient=user).select_related("timesheet")[:limit]


def _get_current_week_timesheet(user):
    if getattr(user, "is_hr_role", False):
        return None
    return user.timesheets.filter(period_start=current_week_start()).select_related("approver").first()


def build_employee_dashboard(user):
    current_timesheet = _get_current_week_timesheet(user)
    reminders = []
    today = get_business_now().date()
    reminder_start = current_week_start() + timedelta(days=2)
    overdue_start = current_week_start() + timedelta(days=4)

    if current_timesheet:
        if current_timesheet.status == Timesheet.Status.IN_PROGRESS:
            if reminder_start <= today < overdue_start:
                reminders.append(
                    {
                        "title": "Submit this week's timesheet",
                        "body": f"Your timesheet for the week starting {current_timesheet.period_start} is due by Thursday.",
                        "severity": "warning",
                    }
                )
            elif today >= overdue_start:
                reminders.append(
                    {
                        "title": "Timesheet overdue",
                        "body": f"Your timesheet for the week starting {current_timesheet.period_start} is now overdue.",
                        "severity": "error",
                    }
                )
        elif current_timesheet.status == Timesheet.Status.REJECTED:
            reminders.append(
                {
                    "title": "Rejected timesheet needs resubmission",
                    "body": f"Update and resubmit the week starting {current_timesheet.period_start}.",
                    "severity": "error",
                }
            )
    elif reminder_start <= today and user.approver_id:
        reminders.append(
            {
                "title": "No current week timesheet started",
                "body": f"You have not started the week beginning {current_week_start()} yet.",
                "severity": "warning" if today < overdue_start else "error",
            }
        )

    return {
        "current_timesheet": current_timesheet,
        "timesheets": user.timesheets.select_related("approver").prefetch_related("entries"),
        "notifications": unread_notifications_for_user(user),
        "reminders": reminders,
    }


def build_approver_dashboard(user):
    today = get_business_now().date()
    pending_reviews = Timesheet.objects.filter(
        approver=user,
        status=Timesheet.Status.SUBMITTED,
    ).select_related("user")
    waiting_for_resubmission = Timesheet.objects.filter(
        approver=user,
        status=Timesheet.Status.REJECTED,
    ).select_related("user")
    missed_submissions = Timesheet.objects.filter(
        approver=user,
        status=Timesheet.Status.IN_PROGRESS,
        submission_due_at__date__lt=today,
    ).select_related("user")

    reminders = []
    due_today = pending_reviews.filter(approval_due_at__date=today)
    overdue = pending_reviews.filter(approval_due_at__date__lt=today)

    if due_today.exists():
        reminders.append(
            {
                "title": "Reviews due today",
                "body": f"You have {due_today.count()} timesheet(s) to complete today.",
                "severity": "warning",
            }
        )
    if overdue.exists():
        reminders.append(
            {
                "title": "Overdue approvals",
                "body": f"You still have {overdue.count()} overdue approval(s) to complete.",
                "severity": "error",
            }
        )

    employee_dashboard = build_employee_dashboard(user)
    current_timesheet = employee_dashboard["current_timesheet"]
    if current_timesheet and current_timesheet.status == Timesheet.Status.IN_PROGRESS:
        reminders.append(
            {
                "title": "Your own timesheet still needs submitting",
                "body": f"Your week starting {current_timesheet.period_start} is still in progress.",
                "severity": "warning",
            }
        )
    elif not current_timesheet and user.approver_id:
        reminders.append(
            {
                "title": "You still need to start your own timesheet",
                "body": f"You do not have a timesheet started for the week beginning {current_week_start()}.",
                "severity": "warning",
            }
        )

    return {
        "pending_reviews": pending_reviews,
        "waiting_for_resubmission": waiting_for_resubmission,
        "missed_submissions": missed_submissions,
        "notifications": Notification.objects.filter(
            recipient=user,
            notification_type__in=[
                Notification.NotificationType.SUBMISSION,
                Notification.NotificationType.RESUBMISSION,
            ],
        ).select_related("timesheet")[:10],
        "reminders": reminders,
    }
