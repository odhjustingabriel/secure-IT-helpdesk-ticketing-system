from pathlib import Path

from django import forms

from .models import Category, Comment, Ticket
from .utils import support_users_queryset

ALLOWED_ATTACHMENT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".doc", ".docx"}
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024


class StyledFormMixin:
    def apply_styles(self):
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-input"


class TicketCreateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "category", "priority", "attachment"]
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
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
        fields = ["status", "priority", "assigned_to", "resolution_note"]
        widgets = {"resolution_note": forms.Textarea(attrs={"rows": 4, "placeholder": "Summarize what was done to resolve or close this ticket."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = support_users_queryset()
        self.fields["assigned_to"].required = False
        self.apply_styles()


class CommentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 4, "placeholder": "Add a helpful update..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("Comment body is required.")
        return body
