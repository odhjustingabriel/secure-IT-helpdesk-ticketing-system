from django.contrib import admin
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from accounts.models import Profile
from .admin import TicketAdmin
from .utils import support_users_queryset
from .models import AuditLog, CannedResponse, Category, Comment, Tag, Ticket
from .views import ticket_queryset_for_user


class TicketWorkflowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Network", description="Network issues")
        self.hardware = Category.objects.create(name="Hardware", description="Device issues")
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
            category=self.hardware,
            priority=Ticket.PRIORITY_LOW,
            status=Ticket.STATUS_PENDING,
            created_by=self.user2,
        )

    def test_ticket_table_queryset_defers_migration_added_fields(self):
        query_sql = str(ticket_queryset_for_user(self.user1).query)
        self.assertNotIn("resolution_note", query_sql)
        self.assertNotIn('"tickets_category"."is_active"', query_sql)

    def test_active_categories_appear_in_ticket_creation_form(self):
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse("ticket_create"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.category, response.context["form"].fields["category"].queryset)

    def test_inactive_categories_do_not_appear_in_ticket_creation_form(self):
        inactive_category = Category.objects.create(name="Retired Systems", description="Old systems", is_active=False)
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse("ticket_create"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(inactive_category, response.context["form"].fields["category"].queryset)

    def test_existing_ticket_with_inactive_category_still_displays(self):
        self.category.is_active = False
        self.category.save()
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)

    def test_user_can_create_ticket(self):
        self.client.login(username="user1", password="pass12345")
        response = self.client.post(
            reverse("ticket_create"),
            {
                "title": "Email down",
                "description": "Mailbox will not load",
                "category": self.category.pk,
                "priority": Ticket.PRIORITY_MEDIUM,
            },
        )
        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(title="Email down")
        self.assertEqual(ticket.created_by, self.user1)
        self.assertTrue(AuditLog.objects.filter(ticket=ticket, action=AuditLog.ACTION_CREATED).exists())

    def test_user_can_view_own_ticket(self):
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VPN issue")

    def test_user_cannot_view_another_users_ticket(self):
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse("ticket_detail", args=[self.other_ticket.pk]))
        self.assertEqual(response.status_code, 403)

    def test_support_staff_can_view_all_tickets(self):
        self.client.login(username="support", password="pass12345")
        response = self.client.get(reverse("ticket_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VPN issue")
        self.assertContains(response, "Printer issue")

    def test_support_staff_can_update_ticket_status(self):
        self.client.login(username="support", password="pass12345")
        response = self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"status": Ticket.STATUS_IN_PROGRESS, "priority": Ticket.PRIORITY_HIGH, "assigned_to": self.support.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.STATUS_IN_PROGRESS)
        self.assertEqual(self.ticket.assigned_to, self.support)

    def test_status_change_creates_audit_log(self):
        self.client.login(username="support", password="pass12345")
        self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"status": Ticket.STATUS_RESOLVED, "priority": Ticket.PRIORITY_HIGH, "assigned_to": "", "resolution_note": "Restarted the VPN service and verified access."},
        )
        self.assertTrue(
            AuditLog.objects.filter(
                ticket=self.ticket,
                action=AuditLog.ACTION_STATUS,
                field_changed="status",
                old_value=Ticket.STATUS_OPEN,
                new_value=Ticket.STATUS_RESOLVED,
            ).exists()
        )

    def test_status_change_sends_email(self):
        self.client.login(username="support", password="pass12345")
        self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"status": Ticket.STATUS_PENDING, "priority": Ticket.PRIORITY_HIGH, "assigned_to": ""},
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["user1@example.com"])
        self.assertIn("Ticket status updated: VPN issue", mail.outbox[0].subject)
        self.assertIn("Updated by: support", mail.outbox[0].body)

    def test_comment_creation_works(self):
        self.client.login(username="user1", password="pass12345")
        response = self.client.post(reverse("ticket_detail", args=[self.ticket.pk]), {"body": "Please help soon."})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(ticket=self.ticket, author=self.user1, body="Please help soon.").exists())
        self.assertTrue(AuditLog.objects.filter(ticket=self.ticket, action=AuditLog.ACTION_COMMENT).exists())


    def test_support_cannot_resolve_ticket_without_resolution_note(self):
        self.client.login(username="support", password="pass12345")
        response = self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"status": Ticket.STATUS_RESOLVED, "priority": Ticket.PRIORITY_HIGH, "assigned_to": "", "resolution_note": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add a resolution note before resolving or closing this ticket.")
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.STATUS_OPEN)

    def test_support_can_resolve_ticket_with_resolution_note(self):
        self.client.login(username="support", password="pass12345")
        response = self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"status": Ticket.STATUS_RESOLVED, "priority": Ticket.PRIORITY_HIGH, "assigned_to": "", "resolution_note": "VPN profile was rebuilt."},
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.STATUS_RESOLVED)
        self.assertEqual(self.ticket.resolution_note, "VPN profile was rebuilt.")

    def test_resolution_note_appears_on_ticket_detail_page(self):
        self.ticket.resolution_note = "Reinstalled VPN and confirmed login."
        self.ticket.save()
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resolution Note")
        self.assertContains(response, "Reinstalled VPN and confirmed login.")

    def test_adding_and_updating_resolution_note_creates_audit_log(self):
        self.client.login(username="support", password="pass12345")
        self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"status": Ticket.STATUS_RESOLVED, "priority": Ticket.PRIORITY_HIGH, "assigned_to": "", "resolution_note": "First fix summary."},
        )
        self.assertTrue(AuditLog.objects.filter(ticket=self.ticket, action=AuditLog.ACTION_RESOLUTION_ADDED).exists())
        self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"status": Ticket.STATUS_RESOLVED, "priority": Ticket.PRIORITY_HIGH, "assigned_to": "", "resolution_note": "Updated fix summary."},
        )
        self.assertTrue(AuditLog.objects.filter(ticket=self.ticket, action=AuditLog.ACTION_RESOLUTION_UPDATED).exists())

    def test_normal_user_cannot_edit_resolution_note(self):
        self.client.login(username="user1", password="pass12345")
        response = self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"status": Ticket.STATUS_RESOLVED, "priority": Ticket.PRIORITY_HIGH, "assigned_to": "", "resolution_note": "User should not set this."},
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.resolution_note)


    def test_ticket_due_at_is_set_from_priority_sla(self):
        self.assertIsNotNone(self.ticket.due_at)
        self.assertGreater(self.ticket.due_at, timezone.now())

    def test_ticket_due_at_is_recalculated_when_priority_changes_without_manual_due_date(self):
        original_due_at = self.ticket.due_at
        self.client.login(username="support", password="pass12345")
        response = self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"status": Ticket.STATUS_OPEN, "priority": Ticket.PRIORITY_CRITICAL, "assigned_to": "", "resolution_note": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.priority, Ticket.PRIORITY_CRITICAL)
        self.assertLess(self.ticket.due_at, original_due_at)
        self.assertGreater(self.ticket.due_at, timezone.now())

    def test_manual_due_at_is_preserved_when_priority_changes(self):
        manual_due_at = timezone.now() + timezone.timedelta(days=10)
        self.client.login(username="support", password="pass12345")
        response = self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {
                "status": Ticket.STATUS_OPEN,
                "priority": Ticket.PRIORITY_CRITICAL,
                "assigned_to": "",
                "due_at": manual_due_at.strftime("%Y-%m-%dT%H:%M"),
                "resolution_note": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.priority, Ticket.PRIORITY_CRITICAL)
        self.assertEqual(self.ticket.due_at.strftime("%Y-%m-%dT%H:%M"), manual_due_at.strftime("%Y-%m-%dT%H:%M"))

    def test_staff_public_comment_sets_first_response(self):
        self.client.login(username="support", password="pass12345")
        response = self.client.post(reverse("ticket_detail", args=[self.ticket.pk]), {"body": "We are checking this now."})
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertIsNotNone(self.ticket.first_response_at)
        self.assertTrue(AuditLog.objects.filter(ticket=self.ticket, action=AuditLog.ACTION_FIRST_RESPONSE).exists())

    def test_internal_note_is_hidden_from_normal_user_and_audited(self):
        self.client.login(username="support", password="pass12345")
        self.client.post(reverse("ticket_detail", args=[self.ticket.pk]), {"body": "Escalated to tier 2.", "is_internal": "on"})
        self.assertTrue(AuditLog.objects.filter(ticket=self.ticket, action=AuditLog.ACTION_INTERNAL_NOTE).exists())
        self.client.logout()
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertNotContains(response, "Escalated to tier 2.")

    def test_staff_can_tag_ticket_and_create_tag_audit_log(self):
        tag = Tag.objects.create(name="Escalated")
        self.client.login(username="support", password="pass12345")
        response = self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"status": Ticket.STATUS_OPEN, "priority": Ticket.PRIORITY_HIGH, "assigned_to": "", "tags": [tag.pk], "due_at": self.ticket.due_at.strftime("%Y-%m-%dT%H:%M"), "resolution_note": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertIn(tag, self.ticket.tags.all())
        self.assertTrue(AuditLog.objects.filter(ticket=self.ticket, action=AuditLog.ACTION_TAGS).exists())

    def test_staff_sees_canned_responses_on_ticket_detail(self):
        CannedResponse.objects.create(title="Password reset", body="Please reset your password from the self-service portal.")
        self.client.login(username="support", password="pass12345")
        response = self.client.get(reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertContains(response, "Canned responses")
        self.assertContains(response, "Password reset")

    def test_ticket_filters_work_at_basic_level(self):
        self.client.login(username="support", password="pass12345")
        response = self.client.get(reverse("ticket_list"), {"status": Ticket.STATUS_PENDING, "priority": Ticket.PRIORITY_LOW})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Printer issue")
        self.assertNotContains(response, "VPN issue")


class TicketAdminTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Security", description="Security issues")
        self.creator = User.objects.create_user("creator", email="creator@example.com", password="pass12345")
        self.staff_user = User.objects.create_user("staffuser", email="staff@example.com", password="pass12345")
        self.staff_user.profile.role = Profile.ROLE_SUPPORT
        self.staff_user.profile.save()
        self.normal_user = User.objects.create_user("normal", email="normal@example.com", password="pass12345")
        self.admin = User.objects.create_superuser("admin", email="admin@example.com", password="adminpass12345")
        self.ticket = Ticket.objects.create(
            title="Screenshot attached",
            description="Please review the attached screenshot.",
            category=self.category,
            priority=Ticket.PRIORITY_MEDIUM,
            created_by=self.creator,
            attachment="ticket_attachments/example.png",
        )

    def test_admin_assignment_queryset_includes_staff_not_normal_users(self):
        assignable_users = support_users_queryset()
        self.assertIn(self.staff_user, assignable_users)
        self.assertNotIn(self.admin, assignable_users)
        self.assertNotIn(self.normal_user, assignable_users)


    def test_admin_can_access_admin_panel_but_staff_cannot(self):
        self.client.login(username="admin", password="adminpass12345")
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
        self.client.logout()
        self.client.login(username="staffuser", password="pass12345")
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)

    def test_admin_ticket_form_assigns_only_staff_role_users(self):
        ticket_admin = TicketAdmin(Ticket, admin.site)
        field = Ticket._meta.get_field("assigned_to")
        form_field = ticket_admin.formfield_for_foreignkey(field, None)
        self.assertIn(self.staff_user, form_field.queryset)
        self.assertNotIn(self.normal_user, form_field.queryset)
        self.assertNotIn(self.admin, form_field.queryset)

    def test_admin_ticket_change_page_shows_attachment_link_and_image_preview(self):
        self.client.login(username="admin", password="adminpass12345")
        response = self.client.get(reverse("admin:tickets_ticket_change", args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "example.png")
        self.assertContains(response, "<img", html=False)
