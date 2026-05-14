from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, TicketCreateForm, TicketUpdateForm
from .models import AuditLog, Category, Ticket
from accounts.permissions import is_support_or_admin
from .utils import create_audit_log, send_status_change_email, support_users_queryset


def ticket_queryset_for_user(user):
    qs = Ticket.objects.select_related("category", "created_by", "assigned_to")
    if is_support_or_admin(user):
        return qs
    return qs.filter(created_by=user)


def apply_ticket_filters(qs, request):
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    category = request.GET.get("category", "")
    assigned_to = request.GET.get("assigned_to", "")
    search = request.GET.get("q", "")
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    if category and category.isdigit():
        qs = qs.filter(category_id=category)
    if assigned_to == "unassigned":
        qs = qs.filter(assigned_to__isnull=True)
    elif assigned_to and assigned_to.isdigit():
        qs = qs.filter(assigned_to_id=assigned_to)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
    return qs


@login_required
def dashboard(request):
    qs = ticket_queryset_for_user(request.user)
    filtered_tickets = apply_ticket_filters(qs, request) if is_support_or_admin(request.user) else qs
    context = {
        "is_staff_role": is_support_or_admin(request.user),
        "tickets": filtered_tickets[:10],
        "categories": Category.objects.all(),
        "support_users": support_users_queryset(),
        "priority_choices": Ticket.PRIORITY_CHOICES,
        "status_choices": Ticket.STATUS_CHOICES,
    }
    if is_support_or_admin(request.user):
        context.update(
            total_tickets=qs.count(),
            open_tickets=qs.filter(status=Ticket.STATUS_OPEN).count(),
            critical_tickets=qs.filter(priority=Ticket.PRIORITY_CRITICAL).count(),
            unassigned_tickets=qs.filter(assigned_to__isnull=True).count(),
        )
    else:
        context.update(
            total_tickets=qs.count(),
            open_tickets=qs.filter(status=Ticket.STATUS_OPEN).count(),
            in_progress_tickets=qs.filter(status=Ticket.STATUS_IN_PROGRESS).count(),
            resolved_tickets=qs.filter(status__in=[Ticket.STATUS_RESOLVED, Ticket.STATUS_CLOSED]).count(),
        )
    return render(request, "tickets/dashboard.html", context)


@login_required
def ticket_list(request):
    qs = apply_ticket_filters(ticket_queryset_for_user(request.user), request)
    return render(
        request,
        "tickets/ticket_list.html",
        {
            "tickets": qs,
            "categories": Category.objects.all(),
            "support_users": support_users_queryset(),
            "priority_choices": Ticket.PRIORITY_CHOICES,
            "status_choices": Ticket.STATUS_CHOICES,
            "is_staff_role": is_support_or_admin(request.user),
        },
    )


@login_required
def ticket_create(request):
    if request.method == "POST":
        form = TicketCreateForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            create_audit_log(request.user, ticket, AuditLog.ACTION_CREATED)
            messages.success(request, "Ticket created successfully.")
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = TicketCreateForm()
    return render(request, "tickets/ticket_form.html", {"form": form})


def get_permitted_ticket(user, pk):
    ticket = get_object_or_404(Ticket.objects.select_related("category", "created_by", "assigned_to"), pk=pk)
    if not is_support_or_admin(user) and ticket.created_by != user:
        raise PermissionDenied("You cannot access another user's ticket.")
    return ticket


@login_required
def ticket_detail(request, pk):
    ticket = get_permitted_ticket(request.user, pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            create_audit_log(request.user, ticket, AuditLog.ACTION_COMMENT)
            messages.success(request, "Comment added.")
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = CommentForm()
    return render(
        request,
        "tickets/ticket_detail.html",
        {
            "ticket": ticket,
            "comments": ticket.comments.select_related("author"),
            "comment_form": form,
            "audit_logs": ticket.audit_logs.select_related("actor") if is_support_or_admin(request.user) else [],
            "is_staff_role": is_support_or_admin(request.user),
        },
    )


@login_required
@user_passes_test(is_support_or_admin)
def ticket_update(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    old_status = ticket.status
    old_priority = ticket.priority
    old_assigned_to = ticket.assigned_to
    old_resolution_note = ticket.resolution_note or ""
    if request.method == "POST":
        form = TicketUpdateForm(request.POST, instance=ticket)
        if form.is_valid():
            updated = form.save()
            if old_status != updated.status:
                create_audit_log(request.user, updated, AuditLog.ACTION_STATUS, "status", old_status, updated.status)
                send_status_change_email(request, updated, old_status, updated.status)
            if old_priority != updated.priority:
                create_audit_log(request.user, updated, AuditLog.ACTION_PRIORITY, "priority", old_priority, updated.priority)
            if old_assigned_to != updated.assigned_to:
                create_audit_log(
                    request.user,
                    updated,
                    AuditLog.ACTION_ASSIGNMENT,
                    "assigned_to",
                    old_assigned_to.username if old_assigned_to else "Unassigned",
                    updated.assigned_to.username if updated.assigned_to else "Unassigned",
                )
            new_resolution_note = updated.resolution_note or ""
            if old_resolution_note != new_resolution_note:
                action = AuditLog.ACTION_RESOLUTION_UPDATED if old_resolution_note else AuditLog.ACTION_RESOLUTION_ADDED
                create_audit_log(request.user, updated, action)
            messages.success(request, "Ticket updated.")
            return redirect("ticket_detail", pk=updated.pk)
    else:
        form = TicketUpdateForm(instance=ticket)
    return render(request, "tickets/ticket_update.html", {"form": form, "ticket": ticket})
