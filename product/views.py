from django.shortcuts import render
from django.http import JsonResponse
from .models import Product
# Create your views here.
def all_product(request):
    products = Product.objects.all()
    product_json = [
        {
            'id' : product.id,
            'product_name': product.product_name,
            'stock': product.stock,
            'price': product.price,
            'description': product.description,
        } for product in products
    ]
    return JsonResponse({'products' : product_json})
