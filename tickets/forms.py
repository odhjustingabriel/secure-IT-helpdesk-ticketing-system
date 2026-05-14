from django import forms

from .models import Comment, Ticket
from .utils import support_users_queryset

ALLOWED_ATTACHMENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.FileInput):
                css = "form-control"
            elif isinstance(widget, forms.Select):
                css = "form-select"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class TicketCreateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "category", "priority", "attachment"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs["maxlength"] = 160
        self.fields["attachment"].help_text = "Optional PDF, image, text, Word document; max 5 MB."
        self._apply_bootstrap()

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Ticket title cannot be empty.")
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
        content_type = getattr(attachment, "content_type", "")
        if content_type and content_type not in ALLOWED_ATTACHMENT_TYPES:
            raise forms.ValidationError("Unsupported file type. Upload a PDF, image, text, or Word document.")
        return attachment


class TicketUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["status", "priority", "assigned_to"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = support_users_queryset()
        self.fields["assigned_to"].required = False
        self._apply_bootstrap()


class CommentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Add a helpful update..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("Comment cannot be empty.")
        return body
