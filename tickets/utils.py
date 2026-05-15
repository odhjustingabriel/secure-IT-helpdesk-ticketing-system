from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.urls import reverse

from accounts.models import Profile
from .models import AuditLog


def staff_users_queryset():
    return User.objects.filter(profile__role=Profile.ROLE_SUPPORT, is_active=True).order_by("username")


def support_users_queryset():
    return staff_users_queryset()


def create_audit_log(actor, ticket, action, field_changed=None, old_value=None, new_value=None):
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        ticket=ticket,
        action=action,
        field_changed=field_changed,
        old_value="" if old_value is None else str(old_value),
        new_value="" if new_value is None else str(new_value),
    )


def send_status_change_email(request, ticket, old_status, new_status):
    detail_path = reverse("ticket_detail", args=[ticket.pk])
    absolute_url = request.build_absolute_uri(detail_path)
    subject = f"Ticket status updated: {ticket.title}"
    body = (
        f"Your ticket status has changed.\n\n"
        f"Ticket: {ticket.title}\n"
        f"Old status: {old_status}\n"
        f"New status: {new_status}\n"
        f"Updated by: {request.user.get_full_name() or request.user.username}\n"
        f"View ticket: {absolute_url}\n"
    )
    if ticket.created_by.email:
        send_mail(subject, body, None, [ticket.created_by.email], fail_silently=True)
