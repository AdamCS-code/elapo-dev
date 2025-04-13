from django.urls import path
from .views import show_order, order_detail, cancel_order, customer_order_list
app_name = 'order'

urlpatterns = [
    path('', customer_order_list, name="show_order"),
    path('/<str:id>/', order_detail, name='order_detail'),
    path('/<str:id>/cancel/', cancel_order, name='cancel_order'),
]
