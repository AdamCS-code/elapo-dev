from django.urls import path
from .views import show_cart, view_cart, edit_product_in_cart, add_product_to_cart, delete_productcart
app_name = 'cart'

urlpatterns = [
    path('', show_cart, name="show_cart"),
    path('view_cart/<str:id>', view_cart, name="view_cart"),
    path('add_product_to_cart', add_product_to_cart, name="add_product_cart"),
    path('edit_product_in_cart', edit_product_in_cart, name="edit_product_cart"),
    path('delete_product_in_cart', delete_productcart, name="delete_product_cart"),
    path('checkout_cart', view_cart, name='checkout_cart'), # create order, set cart to checked out
]
