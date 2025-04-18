# Generated by Django 5.2 on 2025-04-06 08:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WalletAccount',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('pin', models.CharField(max_length=6)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('saldo', models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ('walletAccount', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='wallet.walletaccount')),
            ],
        ),
    ]
