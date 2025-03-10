from django.urls import path
from .views import dashboard_view, faq_edit_or_create_view, load_remaining_faqitems
from livecrowd_help.faqitems.views import autocomplete, faq_delete_view


urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('faq/<int:pk>/edit/', faq_edit_or_create_view, name='faq_edit_or_create'),
    path('faq/create/', faq_edit_or_create_view, name='faq_edit_or_create'),
	path('faq/<int:pk>/delete/', faq_delete_view, name='faq_delete'),
	path('autocomplete/', autocomplete, name='autocomplete'),
	path('load_remaining_faqitems/', load_remaining_faqitems, name='load_remaining_faqitems'),
]