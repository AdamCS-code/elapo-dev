# Generated by Django 5.2 on 2025-04-06 08:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('main', '0003_worker_rating'),
        ('product', '0002_alter_product_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('created_at', models.DateField()),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.customer')),
            ],
        ),
        migrations.CreateModel(
            name='ProductCart',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('quantity', models.PositiveIntegerField()),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cart.cart')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.product')),
            ],
        ),
    ]
