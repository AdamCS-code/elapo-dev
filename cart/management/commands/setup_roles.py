from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from cart.models import Cart, ProductCart

class Command(BaseCommand):
    help = 'Set up groups and assign permissions for Cart and ProductCart models'

    def handle(self, *args, **kwargs):
        groups = {
            'Admin': Group.objects.get_or_create(name='Admin')[0],
            'Worker': Group.objects.get_or_create(name='Worker')[0],
            'Customer': Group.objects.get_or_create(name='Customer')[0],
        }

        model_permissions = {
            Cart: {
                'Customer': ['add_cart', 'delete_cart', 'change_cart', 'view_cart'],
                'Admin': ['view_cart'],
                'Worker': ['view_cart'],
            },
            ProductCart: {
                'Customer': ['add_productcart', 'delete_productcart', 'change_productcart', 'view_productcart'],
                'Admin': ['view_productcart'],
                'Worker': ['view_productcart'],
            }
        }
        
        for model, perms_by_group in model_permissions.items():
            content_type = ContentType.objects.get_for_model(model)
            for group_name, perm_codenames in perms_by_group.items():
                group = groups[group_name]
                for codename in perm_codenames:
                    try:
                        permission = Permission.objects.get(
                            codename=codename,
                            content_type=content_type
                        )
                        group.permissions.add(permission)
                    except Permission.DoesNotExist:
                        self.stderr.write(f"Permission '{codename}' for model '{model.__name__}' not found.")
        
        self.stdout.write(self.style.SUCCESS("Groups and permissions successfully configured."))

