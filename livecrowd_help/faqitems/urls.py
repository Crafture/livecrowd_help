from django.urls import path
from .views import dashboard_view, faq_edit_or_create_view, load_remaining_faqitems
from livecrowd_help.faqitems.views import autocomplete, faq_delete_view, toggle_archive_faq_item, toggle_favorite_event


urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('faq/<int:pk>/edit/', faq_edit_or_create_view, name='faq_edit_or_create'),
    path('faq/create/', faq_edit_or_create_view, name='faq_edit_or_create'),
	path('faq/<int:pk>/delete/', faq_delete_view, name='faq_delete'),
	path('autocomplete/', autocomplete, name='autocomplete'),
	path('load_remaining_faqitems/', load_remaining_faqitems, name='load_remaining_faqitems'),
	path('faq/<int:pk>/archive', toggle_archive_faq_item, name='toggle_archive_faq_item'),
	path('event/<int:event_id>/favorite', toggle_favorite_event, name='toggle_favorite_event')
]