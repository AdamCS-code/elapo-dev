from django.urls import path
from .views import show_order, order_detail, cancel_order, show_order_customer, show_order_worker
app_name = 'order'

urlpatterns = [
    path('order-customer', show_order_customer, name="show_order"),
    path('order-worker', show_order_worker, name='show_order_worker'),
    path('order-gateway', show_order, name='order_gateway'),
    path('<str:id>/', order_detail, name='order_detail'),
    path('<str:id>/cancel/', cancel_order, name='cancel_order'),
]
