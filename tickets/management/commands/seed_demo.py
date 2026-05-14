from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from tickets.models import AuditLog, Category, Comment, Ticket
from tickets.utils import create_audit_log


class Command(BaseCommand):
    help = "Create demo users, categories, tickets, comments, and audit logs."

    def handle(self, *args, **options):
        users = {
            "admin": ("admin12345", Profile.ROLE_ADMIN, True, True, "admin@example.com"),
            "support": ("support12345", Profile.ROLE_SUPPORT, True, False, "support@example.com"),
            "user1": ("user12345", Profile.ROLE_USER, False, False, "user1@example.com"),
            "user2": ("user12345", Profile.ROLE_USER, False, False, "user2@example.com"),
        }
        created_users = {}
        for username, (password, role, is_staff, is_superuser, email) in users.items():
            user, created = User.objects.get_or_create(username=username, defaults={"email": email, "is_staff": is_staff, "is_superuser": is_superuser})
            if created:
                user.set_password(password)
                user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
            created_users[username] = user

        categories = [
            ("Hardware", "Laptops, peripherals, and device issues."),
            ("Network", "VPN, Wi-Fi, connectivity, and firewall requests."),
            ("Software", "Application access and troubleshooting."),
            ("Security", "Security incidents, phishing, and access concerns."),
        ]
        category_map = {name: Category.objects.get_or_create(name=name, defaults={"description": description})[0] for name, description in categories}

        demo_tickets = [
            ("VPN fails after password reset", "User cannot connect to VPN after changing password.", "Network", Ticket.PRIORITY_HIGH, Ticket.STATUS_IN_PROGRESS, "user1", "support"),
            ("Laptop overheating", "Device fan runs constantly and laptop shuts down.", "Hardware", Ticket.PRIORITY_MEDIUM, Ticket.STATUS_OPEN, "user1", None),
            ("Suspicious email reported", "Potential phishing email with attachment received.", "Security", Ticket.PRIORITY_CRITICAL, Ticket.STATUS_PENDING, "user2", "support"),
            ("Request design software install", "Need approved design software for project work.", "Software", Ticket.PRIORITY_LOW, Ticket.STATUS_RESOLVED, "user2", "support"),
        ]
        for title, description, category, priority, status, creator, assignee in demo_tickets:
            ticket, created = Ticket.objects.get_or_create(
                title=title,
                created_by=created_users[creator],
                defaults={
                    "description": description,
                    "category": category_map[category],
                    "priority": priority,
                    "status": status,
                    "assigned_to": created_users[assignee] if assignee else None,
                },
            )
            if created:
                create_audit_log(created_users[creator], ticket, AuditLog.ACTION_CREATED)
                Comment.objects.create(ticket=ticket, author=created_users[creator], body="Initial report submitted for review.")
                create_audit_log(created_users[creator], ticket, AuditLog.ACTION_COMMENT)
                if assignee:
                    create_audit_log(created_users["support"], ticket, AuditLog.ACTION_ASSIGNMENT, "assigned_to", "Unassigned", assignee)

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
