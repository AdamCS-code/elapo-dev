# Generated by Django 5.2 on 2025-04-04 15:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='worker',
            name='rating',
        ),
    ]
