# Generated by Django 5.2 on 2025-04-10 09:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0006_alter_product_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'permissions': [('buy_product', 'Can buy product')]},
        ),
    ]
