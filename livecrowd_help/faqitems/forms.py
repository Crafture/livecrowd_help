# forms.py
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import FAQItem

class FAQItemForm(forms.ModelForm):
    answer = forms.CharField(widget=CKEditor5Widget(config_name="default"))

    class Meta:
        model = FAQItem
        fields = ["question", "answer", "event"]
        

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['user_created'] = forms.CharField(
                initial=self.instance.user_created.name if getattr(self.instance, "user_created", None) else "Unknown",
                disabled=True,
                label="Created By"
            )
            self.fields['user_last_modified'] = forms.CharField(
                initial=self.instance.user_last_modified.name if getattr(self.instance, "user_last_modified", None) else "Unknown",
                disabled=True,
                label="Last Modified By"
            )

class FAQSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Search Query")
    advanced = forms.BooleanField(required=False)
    event_id = forms.IntegerField(required=False)
    venue_id = forms.IntegerField(required=False)
    all = forms.BooleanField(required=False)