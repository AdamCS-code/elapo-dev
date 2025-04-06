from django.urls import path
from .views import all_product

appname = 'product'

urlpatterns = [
    path('all_product', all_product, name='all_product'),
]
