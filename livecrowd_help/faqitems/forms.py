from django import forms
from django.core.validators import FileExtensionValidator
from django_prose_editor.fields import ProseEditorFormField

from .models import FAQItem


class FAQItemForm(forms.ModelForm):
    answer = ProseEditorFormField()

    class Meta:
        model = FAQItem
        fields = ["question", "answer", "event", "tags"]
        widgets = {
            "tags": forms.SelectMultiple(
                attrs={
                    "size": 12,
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["user_created"] = forms.CharField(
                initial=self.instance.user_created.email
                if getattr(self.instance, "user_created", None)
                else "Unknown",
                disabled=True,
                label="Created By",
                required=False,
            )
            self.fields["user_last_modified"] = forms.CharField(
                initial=self.instance.user_last_modified.email
                if getattr(self.instance, "user_last_modified", None)
                else "Unknown",
                disabled=True,
                label="Last Modified By",
                required=False,
            )


class FAQSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Search Query")
    advanced = forms.BooleanField(required=False)
    event_id = forms.IntegerField(required=False)
    venue_id = forms.IntegerField(required=False)
    all = forms.BooleanField(required=False)


class FAQBulkUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV file (columns: question, answer, event, tags)",
        validators=[FileExtensionValidator(allowed_extensions=["csv"])],
    )


class TagBulkUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV file (single column: tag)",
        help_text="CSV must have exactly one header: <code>tag</code>.",
        validators=[FileExtensionValidator(allowed_extensions=["csv"])],
    )
