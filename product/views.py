from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Product
from django.db import connection

@login_required
def all_product(request):
    products = Product.objects.all() 
    product_json = [
        {
            'id' : product.id,
            'product_name': product.product_name,
            'stock': product.stock,
            'price': float(product.price),
            'description': product.description,
        } for product in products
    ]
     
    return JsonResponse(data={'products' : product_json})

def get_product(request):
    with connection.cursor() as cursor:
        cursor.execute("select * from product_product")
        products = cursor.fetchall()
    return JsonResponse({'products': products})