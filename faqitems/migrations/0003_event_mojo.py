# Generated by Django 5.0.11 on 2025-01-31 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faqitems', '0002_remove_event_description_alter_event_start_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='mojo',
            field=models.BooleanField(default=False),
        ),
    ]
