# Generated by Django 5.2 on 2025-04-10 09:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0004_alter_cart_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cart',
            options={'permissions': [('checkout_cart', 'can checkout cart')]},
        ),
    ]
