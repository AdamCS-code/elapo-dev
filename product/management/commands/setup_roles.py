from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from product.models import Product

class Command(BaseCommand):
    help = 'set up groups and permissions'

    def handle(self, *args, **kwargs):
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        worker_group, _ = Group.objects.get_or_create(name='Worker')
        customer_group, _ = Group.objects.get_or_create(name='Customer')

        # get permissions
        content_type = ContentType.objects.get_for_model(Product)
        add_product_permission = Permission.objects.get(
            codename='add_product',
            content_type=content_type
        )
        admin_group.permissions.add(add_product_permission)

        buy_product_permission = Permission.objects.get(
            codename='buy_product',
            content_type=content_type
        )
        customer_group.permissions.add(buy_product_permission)

