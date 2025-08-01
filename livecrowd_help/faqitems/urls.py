from django.urls import path

from livecrowd_help.faqitems.views import autocomplete
from livecrowd_help.faqitems.views import faq_delete_view
from livecrowd_help.faqitems.views import toggle_archive_faq_item
from livecrowd_help.faqitems.views import toggle_favorite_event

from .views import dashboard_view
from .views import faq_bulk_upload_view
from .views import faq_edit_or_create_view
from .views import load_remaining_faqitems
from .views import tag_bulk_upload_view

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("faq/<int:pk>/edit/", faq_edit_or_create_view, name="faq_edit_or_create"),
    path("faq/create/", faq_edit_or_create_view, name="faq_edit_or_create"),
    path("faq/<int:pk>/delete/", faq_delete_view, name="faq_delete"),
    path(
        "faq/upload-multiple/",
        faq_bulk_upload_view,
        name="faq_bulk_upload_view",
    ),
    path(
        "tag/upload-multiple/",
        tag_bulk_upload_view,
        name="tag_bulk_upload_view",
    ),
    path("autocomplete/", autocomplete, name="autocomplete"),
    path(
        "load_remaining_faqitems/",
        load_remaining_faqitems,
        name="load_remaining_faqitems",
    ),
    path(
        "faq/<int:pk>/archive",
        toggle_archive_faq_item,
        name="toggle_archive_faq_item",
    ),
    path(
        "event/<int:event_id>/favorite",
        toggle_favorite_event,
        name="toggle_favorite_event",
    ),
]
