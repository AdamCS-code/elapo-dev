from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from .models import Cart, ProductCart
from product.models import Product
from order.models import Order, OrderStatus
from main.models import Customer
import json

@login_required
@require_POST
@permission_required('cart.delete_cart')
def delete_cart(request):
    data = json.loads(request.body)
    id = data['cart_id']
    try:
        cart = Cart.objects.get(pk=id)
        cart.delete()
        print('deleted')
    except Cart.DoesNotExist:
        return JsonResponse({'error': 'failed to delete, cannot find cart'}, status=400)
    return JsonResponse({'message': 'success to delete cart'}, status=200)

@login_required
@require_POST
@permission_required('cart.delete_productcart')
def delete_productcart(request):
    data = json.loads(request.body)
    product_cart_id = data['productcart_id']
    try:
        product_cart = ProductCart.objects.get(id=product_cart_id)
        product_cart.delete()
    except ProductCart.DoesNotExist:
        return JsonResponse({'error': 'product cart is not found'}, status=400)
    return JsonResponse({'success': 'delete product'}, status=200)

@login_required
@permission_required('cart.view_productcart')
def show_cart(request):
    cart = Cart.objects
    try:
        customer = Customer.objects.get(user=request.user)
        cart = cart.filter(customer=customer, is_checked_out=False).first()
        
        if not cart:
            cart = Cart.objects.create(customer=customer, is_checked_out=False)
    except Customer.DoesNotExist:
        return JsonResponse({'status': 'failed to access cart page, you are not customer'})
    return render(request, 'show_cart.html', context={'cart_id': str(cart.id)})

@login_required
@permission_required("cart.checkout_cart")
def checkout_cart(request):
    data = json.loads(request.body)
    cart_id = data['cart_id']
    total = data['total']
    print(data)
    try:
        status = OrderStatus.objects.filter(status='not paid').first()
    except OrderStatus.DoesNotExist:
        return JsonResponse({'message': 'fail'})
    
    try:
        cart = Cart.objects.get(id=cart_id)
        cart.is_checked_out = True
        cart.save()
    except Cart.DoesNotExist:
        return JsonResponse({'message': 'fail'})
    
    Order.objects.create(
        cart=cart,
        status_id=status.id,
        total=total
    )

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
    data = json.loads(request.body)
    try:
        product_cart = data['product_cart_id']
        product_cart = ProductCart.objects.get(id=product_cart)
    except ProductCart.DoesNotExist:
        JsonResponse({'message': 'product cart is not found'})

    product_cart_quantity = int(data['amount'])

    print(product_cart_quantity)
    
    if product_cart_quantity == 0:
        product_cart.delete()
    elif product_cart_quantity < 0 or product_cart_quantity > product_cart.product.stock:
        return JsonResponse({'message': f'product quantity must be greater than 0 and less than {product_cart.product.stock}'}, status=400)
    product_cart.quantity = product_cart_quantity
    product_cart.save()
    return JsonResponse({"product_cart": product_cart.id, 'message': 'success'}, status=200)

@login_required
@require_POST
@permission_required('cart.add_productcart', 'cart.change_cart','cart.view_cart')
def add_product_to_cart(request):
    data = json.loads(request.body)
    product = data['product_id']
    amount = int(data['amount'])
    try:
        product = Product.objects.get(pk=product)

    except Product.DoesNotExist:
        return JsonResponse({'message': 'Product does not exist'}, status=400)

    if amount < 1:
        return JsonResponse({'message': 'Amount has to be positive integer'}, status=400) 

    customer = Customer.objects.get(user=request.user)

    cart = Cart.objects.filter(customer=customer, is_checked_out=False).first()
    if not cart:
        cart = Cart.objects.create(customer=customer)
    product_cart, created = ProductCart.objects.get_or_create(cart=cart, product=product)
    print(product_cart)
    product_quantity = product_cart.quantity
    product_quantity += amount
    print(product_quantity)

    if product_quantity > product.stock:
        return JsonResponse({'message': 'Out of stock'}, status=400)

    product_cart.quantity = product_quantity 
    product_cart.save()
    return JsonResponse({'message': 'success'}, status=200)
