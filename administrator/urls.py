from django.urls import path
<<<<<<< HEAD
from .views import dashboard

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
]
=======
from . import views

app_name = 'administrator'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('no-permission/', views.no_permission, name='no_permission'),
    path('all_product/', views.all_product, name='all_product'),
    path('get_product/', views.get_product, name='get_product'),
    path('create_product/', views.create_product, name='create_product'),
    path('update_product/<uuid:product_id>/', views.update_product, name='update_product'),
    path('delete_product/<uuid:product_id>/', views.delete_product, name='delete_product'),
    path('process-order/<uuid:order_id>/', views.process_order, name='process_order'),
    path('product_dashboard/', views.product_dashboard, name='product_dashboard')
]

>>>>>>> unittest
