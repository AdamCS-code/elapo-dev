from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from main.models import Customer
from cart.models import ProductCart, Cart
from .models import Order, OrderStatus
from wallet.models import WalletAccount, Wallet
import json, uuid

NOT_PAID_STATUS_ID = '11111111111111111111111111111111'
PAID_STATUS_ID = '22222222222222222222222222222222'
PREPARED_STATUS_ID = '33333333333333333333333333333333'
READY_STATUS_ID = '44444444444444444444444444444444'
DELIVERED_STATUS_ID = '55555555555555555555555555555555'
COMPLETED_STATUS_ID = '66666666666666666666666666666666'
REVIEWED_STATUS_ID = '77777777777777777777777777777777'
CANCELLED_STATUS_ID = '88888888888888888888888888888888'

def update_wallet_ballance(wallet, amount):
    wallet.saldo = amount
    wallet.save()

def update_product(cart):
    product_carts = ProductCart.objects.filter(cart=cart)
    for product_cart in product_carts:
        product_cart.product.stock += product_cart.quantity
        product_cart.product.save()

@login_required
def show_order(request):
    return render(request, 'show_order.html', context={})

@login_required
def customer_view_order(request):
    customer = request.user.customer

    if not customer:
        return JsonResponse({'message': 'customer not found? are you customer?'})

    status_count = dict() 

    order = Order.objects.filter(cart__customer=customer)
    orderStatus = OrderStatus.objects.all().order_by('id') 

    for status in orderStatus:
        status_count[status.status] = order.filter(status=status).count()

    active_status_id = request.GET.get('status', status.first().id if status.exists() else None)

    if active_status_id:
        active_orders = Order.objects.filter(
                status_id=active_status_id,
                cart__customer=customer
            ).select_related('cart', 'status').order_by('-created_at')
    else:
        active_orders = []
    
    return render(request, 'show_order.html', context = {
        'statuses': status,
            'status_counts': status_count,
            'active_status_id': active_status_id,
            'active_orders': active_orders
    })

@login_required
def customer_order_list(request):
    orders = Order.objects.filter(cart__customer=request.user.customer).select_related('status')
    not_paid_orders = orders.filter(status__status='not paid')
    paid_orders = orders.filter(status__status='paid')
    prepared_orders = orders.filter(status__status='prepared')
    ready_orders = orders.filter(status__status='ready')
    delivered_orders = orders.filter(status__status='delivered')
    completed_orders = orders.filter(status__status='completed')
    reviewed_orders = orders.filter(status__status='reviewed')
    cancelled_orders = orders.filter(status__status='cancelled')
    print(orders)
    context = {
        'not_paid_orders': not_paid_orders,
        'paid_orders': paid_orders,
        'prepared_orders': prepared_orders,
        'ready_orders': ready_orders,
        'delivered_orders': delivered_orders,
        'completed_orders': completed_orders,
        'reviewed_orders': reviewed_orders,
        'cancelled_orders': cancelled_orders,
    }
    return render(request, 'show_order.html', context)

@login_required
def order_detail(request, id):
    order = get_object_or_404(Order, id=id)
    if order.cart.customer != request.user.customer:
        messages.error(request, "You don't have permission to view this order.")
        return redirect('order:show_order')
    product_carts = ProductCart.objects.filter(cart=order.cart)

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
    context = {
        'order': order,
        'cart_products': product_carts_json,
        'can_cancel': str(order.status.status) in [
            'not paid',
            'paid',
        ]
    }
    return render(request, 'show_order_details.html', context)

@login_required
@permission_required('order.set_to_cancelled')
def cancel_order(request, id):
    order = get_object_or_404(Order, id=id)
    
    if order.cart.customer != request.user.customer:
        messages.error(request, "You don't have permission to cancel this order.")
        return redirect('order:show_order')
    
    cancellable_statuses = [
        'not paid',
        'paid',
    ]
    
    if order.status.status not in cancellable_statuses:
        messages.error(request, "This order cannot be cancelled at its current status.")
        return redirect('order:order_detail', id=id)

    if order.status.id == uuid.UUID(PAID_STATUS_ID):
        update_product(order.cart)
        wallet = Wallet.objects.get(walletAccount__user = request.user)
        update_wallet_ballance(wallet, wallet.saldo+order.total)

    cancelled_status = OrderStatus.objects.get(id='88888888888888888888888888888888')
    order.status = cancelled_status
    order.save()
    
    messages.success(request, "Your order has been cancelled successfully.")
    return redirect('order:order_detail', id=id)


