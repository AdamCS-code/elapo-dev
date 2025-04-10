from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_GET, require_POST
from .models import Cart, ProductCart
from product.models import Product
from main.models import Customer
import json
import uuid

@login_required
@require_POST
def add_cart(request, id):
    data = json.loads(request.body)

    return

@login_required
@permission_required('cart.delete_cart')
def delete_cart(request, id):
    try:
        cart = Cart.objects.get(cart_id=id)
        cart.delete()
    except Cart.DoesNotExist:
        return JsonResponse({'status': 'failed to delete, cannot find cart'})
    return JsonResponse({'status': 'success to delete cart'})

@login_required
def show_cart(request):
    cart = Cart.objects
    try:
        customer = Customer.objects.get(user=request.user)
        cart = cart.filter(customer=customer, is_checked_out=False).first()
    except Customer.DoesNotExist:
        return JsonResponse({'status': 'failed to access cart page, you are not customer'})
    return render(request, 'show_cart.html', context={'cart_id': str(cart.id)})

@login_required
@permission_required("cart.checkout_cart")
def checkout_cart(request):
    return JsonResponse({'status': 'success'})

@login_required
@permission_required('cart.view_cart')
def view_cart(request, id):
    cart = Cart.objects
    try:
        cart = cart.get(pk=id)
    except Cart.DoesNotExist:
        print('error')
        return JsonResponse({'status': 'cannot get cart object with such uuid'})

    product_carts = ProductCart.objects.filter(cart_id=cart)
    
    product_carts_json = [
        {
            'product' : {
                'product_id': product_cart.product.id,
                'product_name': product_cart.product.product_name,
                'product_stock': product_cart.product.stock,
                'product_price': product_cart.product.price,
                'product_description': product_cart.product.description
            },
            'id': product_cart.id,
            'quantity': product_cart.quantity,
        } for product_cart in product_carts
    ]
    print(product_carts)
    return JsonResponse({'product_carts': product_carts_json})

@login_required
@permission_required("cart.change_cart")
def edit_product_in_cart(request):
    return JsonResponse({})

@login_required
@require_POST
@permission_required('cart.add_productcart', 'cart.change_cart','cart.view_cart')
def add_product_to_cart(request):
    product = request.POST.get('product_id')
    amount = request.POST.get('amount')

    try:
        product = Product.objects.get(pk=uuid.UUID(product))

    except Product.DoesNotExist:
        return JsonResponse({'status': 'Product does not exist'})

    if amount < 1:
        return JsonResponse({'status': 'Amount has to be positive integer'}) 

    customer = Customer.objects.get(user=request.user)
    cart = Cart.objects.filter(customer=customer, is_checked_out=False).first()
    if not cart:
        cart = Cart.objects.create(customer=customer)
    product_cart, created = ProductCart.objects.get_or_create(cart=cart, product=product)
    product_quantity = product_cart.quantity
    product_quantity += amount

    if product_quantity > product.stock:
        return JsonResponse({'status': 'Out of stock'})

    product_cart.quantity = product_quantity 
    product_cart.save()
    return JsonResponse({'status': 'success to add product'})

@login_required
def change_productcart(request):
    return
