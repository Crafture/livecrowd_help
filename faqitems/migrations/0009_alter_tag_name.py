# Generated by Django 5.0.11 on 2025-02-03 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faqitems', '0008_alter_event_venue_alter_faqitem_event'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(default='general', max_length=255, unique=True),
        ),
    ]
