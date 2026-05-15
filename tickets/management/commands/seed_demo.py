from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from tickets.models import AuditLog, CannedResponse, Category, Comment, Tag, Ticket
from tickets.utils import create_audit_log


class Command(BaseCommand):
    help = "Create demo users, categories, tickets, comments, and audit logs."

    def handle(self, *args, **options):
        users = {
            "admin": ("admin12345", Profile.ROLE_ADMIN, True, True, "admin@example.com"),
            "support": ("support12345", Profile.ROLE_SUPPORT, False, False, "support@example.com"),
            "user1": ("user12345", Profile.ROLE_USER, False, False, "user1@example.com"),
            "user2": ("user12345", Profile.ROLE_USER, False, False, "user2@example.com"),
        }
        created_users = {}
        for username, (password, role, is_staff, is_superuser, email) in users.items():
            user, created = User.objects.get_or_create(username=username, defaults={"email": email})
            user.email = email
            user.is_staff = is_staff
            user.is_superuser = is_superuser
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

        tag_map = {
            name: Tag.objects.get_or_create(name=name, defaults={"color": color})[0]
            for name, color in [("VPN", "#047857"), ("Security", "#DC2626"), ("Hardware", "#2563EB"), ("Access", "#7C3AED")]
        }
        CannedResponse.objects.get_or_create(
            title="Request more details",
            defaults={"body": "Thanks for reporting this. Could you share the exact error message and when the issue started?"},
        )
        CannedResponse.objects.get_or_create(
            title="Issue resolved",
            defaults={"body": "This issue has been resolved. Please reply if you see the problem again."},
        )

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
                if "VPN" in title:
                    ticket.tags.add(tag_map["VPN"], tag_map["Access"])
                if "Suspicious" in title:
                    ticket.tags.add(tag_map["Security"])
                if "Laptop" in title:
                    ticket.tags.add(tag_map["Hardware"])
                if assignee:
                    create_audit_log(created_users["support"], ticket, AuditLog.ACTION_ASSIGNMENT, "assigned_to", "Unassigned", assignee)

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
