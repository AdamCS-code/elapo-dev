# Generated by Django 5.2 on 2025-04-13 07:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_worker_rating'),
        ('wallet', '0006_alter_orderpayment_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderpayment',
            name='customer',
        ),
        migrations.AlterField(
            model_name='orderpayment',
            name='worker',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main.worker'),
        ),
    ]
