# forms.py
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import FAQItem

class FAQItemForm(forms.ModelForm):
    answer = forms.CharField(widget=CKEditor5Widget(config_name="default"))

    class Meta:
        model = FAQItem
        fields = ["question", "answer", "event"]