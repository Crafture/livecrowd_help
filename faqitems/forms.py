# forms.py
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import FAQItem

class FAQItemForm(forms.ModelForm):
    answer = forms.CharField(widget=CKEditor5Widget(config_name="default"))

    class Meta:
        model = FAQItem
        fields = ["question", "answer", "event"]

class FAQSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Search Query")
    advanced = forms.BooleanField(required=False)
    event_id = forms.IntegerField(required=False)
    venue_id = forms.IntegerField(required=False)
    all = forms.BooleanField(required=False)