from django.db import models
from autoslug import AutoSlugField
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model


# Models

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_created = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_%(class)s",
    )
    user_last_modified = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="modified_%(class)s",
    )

    class Meta:
        abstract = True

class Venue(TimestampedModel):
    display_name = models.CharField(max_length=200, default="Unknown Venue")
    slug = AutoSlugField(populate_from='display_name', editable=False)

    def __str__(self):
        return self.display_name


class Tag(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        default="general"  # Default tag if none is provided
    )

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Event(TimestampedModel):
    display_name = models.CharField(max_length=400, default="Untitled Event")
    slug = AutoSlugField(populate_from='display_name', editable=False)
    start_date = models.DateField(auto_now_add=True)  # Default to the current date
    mojo = models.BooleanField(default=False)
    venue = models.ForeignKey(
        Venue, on_delete=models.CASCADE, default=4
    )  # Assuming a Venue with ID 1 exists
    tags = models.ManyToManyField(Tag, related_name='events')

    def __str__(self):
        return self.display_name
    
    class Meta:
        ordering = ['display_name']


class FAQItem(TimestampedModel):
    question = models.CharField(max_length=255, default="No question provided")
    answer = models.TextField(default="No answer available")
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, default=4
    )  # Assuming an Event with ID 1 exists
    tags = models.ManyToManyField(Tag, related_name="faqs")

    def __str__(self):
        return self.question
    
