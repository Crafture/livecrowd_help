from django.contrib.auth import get_user_model
from django.db import models
from django.utils.html import strip_tags
from django_extensions.db.fields import AutoSlugField
from django_prose_editor.fields import ProseEditorField


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_created = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_%(class)s",
    )
    user_last_modified = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modified_%(class)s",
    )

    class Meta:
        abstract = True


class Venue(TimestampedModel):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from=["name"], overwrite=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=255,
    )
    slug = AutoSlugField(populate_from=["name"], overwrite=True)

    class Meta:
        permissions = [("add_tags_with_csv", "Add tags with CSV")]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)


class Event(TimestampedModel):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from=["name"], overwrite=True)
    start_date = models.DateField(auto_now_add=True)
    mojo = models.BooleanField(default=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, null=True)
    tags = models.ManyToManyField(Tag, related_name="events")
    favorite = models.BooleanField(default=False)

    class Meta:
        ordering = ["updated_at"]

    def __str__(self):
        return self.name


class FAQItem(TimestampedModel):
    question = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from=["question"], overwrite=True)
    answer = ProseEditorField(
        max_length=4096,
        extensions={
            "Bold": True,
            "Italic": True,
            "BulletList": True,
            "Link": True,
            "OrderedList": True,
            "Blockquote": True,
            "Strike": True,
            "Underline": True,
            "HardBreak": True,
            "Table": True,
            "History": True,
            "HTML": True,
            "Typographic": True,
        },
        sanitize=True,
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True)
    tags = models.ManyToManyField(Tag, related_name="faqs")
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["updated_at"]
        permissions = [("add_faqitems_with_csv", "Add FAQs with CSV")]

    def __str__(self):
        return self.question

    @property
    def answer_clean(self) -> str:
        return strip_tags(self.answer)
