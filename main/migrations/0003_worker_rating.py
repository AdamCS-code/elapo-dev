# Generated by Django 5.2 on 2025-04-05 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_remove_worker_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='worker',
            name='rating',
            field=models.IntegerField(default=0),
        ),
    ]
