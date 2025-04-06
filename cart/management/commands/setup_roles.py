from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from cart.models import Cart, ProductCart

class Command(BaseCommand):
    help = 'set up groups and permission'

    def handle(self, *args, **kwargs):
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        worker_group, _ = Group.objects.get_or_create(name='Worker')
        customer_group, _ = Group.objects.get_or_create(name='Customer')

        content_type = ContentType.objects.get_for_model(Cart) 

        privileges = ['add_cart', 'delete_cart', 'change_cart', 'view_cart']
        for privilege in privileges:
            permission = Permission.objects.get(
                codename=privilege,
                content_type=content_type
            )
            customer_group.permissions.add(permission)

        view_cart_permission = Permission.objects.get(
            codename='view_cart',
            content_type=content_type
        )
        admin_group.permissions.add(view_cart_permission)
        worker_group.permissions.add(view_cart_permission)

        content_type = ContentType.objects.get_for_model(ProductCart)
        
        privileges = ['add_productcart', 'delete_productcart', 'change_productcart', 'view_productcart']
        for privilege in privileges:
            permission = Permission.objects.get(
                codename=privilege,
                content_type=content_type
            )
            customer_group.permissions.add(permission)
        
        view_productcart_permission = Permission.objects.get(
            codename='view_productcart',
            content_type=content_type
        )
        admin_group.permissions.add(view_productcart_permission)
        worker_group.permissions.add(view_productcart_permission)
