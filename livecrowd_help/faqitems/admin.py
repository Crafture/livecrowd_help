from django.contrib import admin
from .models import Venue, Event, Tag, FAQItem

# Register your models here.

class CustomAdmin(admin.ModelAdmin):
    readonly_fields = ('user_created', 'user_last_modified')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user_created = request.user
        obj.user_last_modified = request.user
        super().save_model(request, obj, form, change)


@admin.register(Venue)
class VenueAdmin(CustomAdmin):
	pass

@admin.register(Event)
class EventAdmin(CustomAdmin):
    pass

@admin.register(FAQItem)
class FAQItemAdmin(CustomAdmin):
    pass

admin.site.register(Tag)