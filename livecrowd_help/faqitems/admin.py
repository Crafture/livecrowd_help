from django.contrib import admin

from .models import Event
from .models import FAQItem
from .models import Tag
from .models import Venue


class CustomAdmin(admin.ModelAdmin):
    readonly_fields = ["user_created", "user_last_modified", "slug"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user_created = request.user
        obj.user_last_modified = request.user
        super().save_model(request, obj, form, change)


@admin.register(Venue)
class VenueAdmin(CustomAdmin):
    search_fields = ["name", "slug"]
    ordering = ["name"]
    list_display = ["name", "slug"]


@admin.register(Event)
class EventAdmin(CustomAdmin):
    search_fields = ["name", "slug"]
    ordering = ["name"]
    list_display = ["name", "slug"]


@admin.register(FAQItem)
class FAQItemAdmin(CustomAdmin):
    list_display = ["question", "updated_at", "user_created", "user_last_modified"]
    ordering = ["-updated_at"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug"]
    ordering = ["name"]
