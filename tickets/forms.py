from pathlib import Path

from django import forms

from .models import Category, Comment, Tag, Ticket
from .utils import staff_users_queryset

ALLOWED_ATTACHMENT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".doc", ".docx"}
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024


class StyledFormMixin:
    def apply_styles(self):
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-input"


class TicketCreateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "category", "priority", "channel", "attachment"]
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        self.fields["channel"].required = False
        self.fields["channel"].initial = Ticket.CHANNEL_PORTAL
        self.fields["title"].widget.attrs["maxlength"] = 160
        self.fields["attachment"].help_text = "Optional PDF, PNG, JPG, TXT, DOC, or DOCX file up to 5 MB."
        self.apply_styles()

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Ticket title is required.")
        return title

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if not description:
            raise forms.ValidationError("Description is required.")
        return description

    def clean_channel(self):
        return self.cleaned_data.get("channel") or Ticket.CHANNEL_PORTAL

    def clean_attachment(self):
        attachment = self.cleaned_data.get("attachment")
        if not attachment:
            return attachment
        if attachment.size > MAX_ATTACHMENT_SIZE:
            raise forms.ValidationError("Attachment must be 5 MB or smaller.")
        extension = Path(attachment.name).suffix.lower()
        if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
            raise forms.ValidationError("Unsupported file type. Upload PDF, PNG, JPG, JPEG, TXT, DOC, or DOCX only.")
        return attachment


class TicketUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["status", "priority", "assigned_to", "tags", "due_at", "resolution_note"]
        widgets = {
            "resolution_note": forms.Textarea(attrs={"rows": 4, "placeholder": "Summarize what was done to resolve or close this ticket."}),
            "tags": forms.CheckboxSelectMultiple,
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = staff_users_queryset()
        self.fields["assigned_to"].required = False
        self.fields["tags"].queryset = Tag.objects.filter(is_active=True)
        self.fields["tags"].required = False
        self.fields["due_at"].required = False
        self.fields["due_at"].help_text = "SLA target. Leave as-is unless the support lead approves an adjustment."
        self.fields["resolution_note"].required = False
        self.fields["resolution_note"].help_text = "Required when setting the ticket status to resolved or closed."
        self.apply_styles()

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        resolution_note = (cleaned_data.get("resolution_note") or "").strip()
        if status in {Ticket.STATUS_RESOLVED, Ticket.STATUS_CLOSED} and not resolution_note:
            self.add_error("resolution_note", "Add a resolution note before resolving or closing this ticket.")
        cleaned_data["resolution_note"] = resolution_note
        return cleaned_data

    def save(self, commit=True):
        ticket = super().save(commit=False)
        priority_changed = "priority" in self.changed_data
        due_at_manually_changed = "due_at" in self.changed_data
        if priority_changed and not due_at_manually_changed:
            ticket.due_at = ticket.calculate_due_at()
        if commit:
            ticket.save()
            self.save_m2m()
        return ticket


class CommentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body", "is_internal"]
        widgets = {"body": forms.Textarea(attrs={"rows": 4, "placeholder": "Add a helpful update..."})}

    def __init__(self, *args, is_staff_role=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_staff_role:
            self.fields.pop("is_internal")
        else:
            self.fields["is_internal"].required = False
            self.fields["is_internal"].help_text = "Internal notes are visible to staff/admin only."
        self.apply_styles()

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("Comment body is required.")
        return body
