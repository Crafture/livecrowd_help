# Generated by Django 5.0.11 on 2025-01-31 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faqitems', '0005_event_user_created_event_user_last_modified_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
