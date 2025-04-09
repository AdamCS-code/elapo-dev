from django.urls import path
from .views import all_product

app_name = 'product'

urlpatterns = [
    path('all_product', all_product, name='all_product'),
]
