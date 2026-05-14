from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from .models import AuditLog, Category, Comment, Ticket


class TicketWorkflowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Network", description="Network issues")
        self.user1 = User.objects.create_user("user1", email="user1@example.com", password="pass12345")
        self.user2 = User.objects.create_user("user2", email="user2@example.com", password="pass12345")
        self.support = User.objects.create_user("support", email="support@example.com", password="pass12345")
        self.support.profile.role = Profile.ROLE_SUPPORT
        self.support.profile.save()
        self.ticket = Ticket.objects.create(
            title="VPN issue",
            description="Cannot connect",
            category=self.category,
            priority=Ticket.PRIORITY_HIGH,
            created_by=self.user1,
        )
        self.other_ticket = Ticket.objects.create(
            title="Printer issue",
            description="Paper jam",
            category=self.category,
            priority=Ticket.PRIORITY_LOW,
            status=Ticket.STATUS_PENDING,
            created_by=self.user2,
        )

    def test_user_can_create_ticket(self):
        self.client.login(username="user1", password="pass12345")
        response = self.client.post(reverse("ticket_create"), {
            "title": "Email down",
            "description": "Mailbox will not load",
            "category": self.category.pk,
            "priority": Ticket.PRIORITY_MEDIUM,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ticket.objects.filter(title="Email down", created_by=self.user1).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.ACTION_CREATED, ticket__title="Email down").exists())

    def test_user_cannot_view_another_users_ticket(self):
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse("ticket_detail", args=[self.other_ticket.pk]))
        self.assertEqual(response.status_code, 403)

    def test_support_staff_can_view_all_tickets(self):
        self.client.login(username="support", password="pass12345")
        response = self.client.get(reverse("ticket_list"))
        self.assertContains(response, "VPN issue")
        self.assertContains(response, "Printer issue")

    def test_support_staff_can_change_ticket_status_with_audit_and_email(self):
        self.client.login(username="support", password="pass12345")
        response = self.client.post(reverse("ticket_update", args=[self.ticket.pk]), {
            "status": Ticket.STATUS_IN_PROGRESS,
            "priority": self.ticket.priority,
            "assigned_to": self.support.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.STATUS_IN_PROGRESS)
        self.assertTrue(AuditLog.objects.filter(ticket=self.ticket, action=AuditLog.ACTION_STATUS, field_changed="status").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Ticket status updated: VPN issue", mail.outbox[0].subject)

    def test_comment_creation_works(self):
        self.client.login(username="user1", password="pass12345")
        response = self.client.post(reverse("ticket_detail", args=[self.ticket.pk]), {"body": "Any update?"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(ticket=self.ticket, body="Any update?").exists())
        self.assertTrue(AuditLog.objects.filter(ticket=self.ticket, action=AuditLog.ACTION_COMMENT).exists())

    def test_ticket_list_filters_work(self):
        self.client.login(username="support", password="pass12345")
        response = self.client.get(reverse("ticket_list"), {"status": Ticket.STATUS_PENDING})
        self.assertContains(response, "Printer issue")
        self.assertNotContains(response, "VPN issue")
