from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from product.models import Product
from cart.models import Cart, ProductCart
from order.models import Order, OrderStatus

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
        
        print("setup roles pada product berhasil")
        
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

        content_type = ContentType.objects.get_for_model(Order)
        # customer privileges
        privileges = [
            "set to paid",
            "set to prepared",
            "set to ready",
            "set to delivered",
            "set to completed",
            "set to cancelled",
            "set to reviewed",
        ]

        customer_privileges = [0, 5, 6]
        worker_privileges = [3, 4]
        admin_privileges = [1,2]
        
        for cust_privilege in customer_privileges:
            permission = Permission.objects.get(
                codename=privileges[cust_privilege],
                content_type=content_type
            )
            customer_group.permissions.add(permission)
       
        for work_privilege in worker_privileges:
            permission = Permission.objects.get(
                codename=privileges[work_privilege],
                content_type=content_type
            )
            worker_group.permissions.add(permission)
        
        for admin_privilege in worker_privileges:
            permission = Permission.objects.get(
                codename=privileges[admin_privilege],
                content_type=content_type
            )
            admin_group.permissions.add(permission)

        print("setup roles pada order berhasil")

        print("setup roles pada cart berhasil")
        print("setup roles done\nrun this command:\nsqlite3 db.sqlite3\nselect * from auth_group_permissions;")



