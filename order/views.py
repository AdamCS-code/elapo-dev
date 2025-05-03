from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from main.models import Customer
from cart.models import ProductCart, Cart
from .models import Order, OrderStatus
from wallet.models import WalletAccount, Wallet, OrderPayment
import json, uuid
from core.views import get_user_role
from django.http import JsonResponse

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
    context = {'user': request.user}
    if get_user_role(request.user) == 'Customer':
        return redirect('order:show_order')
    elif get_user_role(request.user) == 'Worker':
        return redirect('order:show_order_worker')
    elif get_user_role(request.user) == 'Admin':
        return redirect('order:show_order_admin')
    return render(request, 'show_order.html', context)

@login_required
def show_order_admin(request):

    if get_user_role(request.user) == 'Admin':
        available_orders = OrderPayment.objects.filter(order__status__status='paid')
        prepared_orders = OrderPayment.objects.filter(order__status__status='prepared')
        reviewed_orders = OrderPayment.objects.filter(order__status__status='reviewed')
        context = {
            'paid_orders': available_orders,
            'prepared_orders': prepared_orders,
            'reviewed_orders': reviewed_orders,
            'is_admin': True,
        }
        return render(request, 'show_order_admin.html', context)
    else:
       return JsonResponse({'message': 'only admin could access this resource!'}, status=400) 
        
@login_required
def show_order_worker(request):
    if get_user_role(request.user) == 'Worker':
        available_orders = OrderPayment.objects.filter(worker__isnull=True, order__status__status='ready')
        delivered_orders = OrderPayment.objects.filter(worker=request.user.worker, order__status__status='delivered') 
        completed_orders = OrderPayment.objects.filter(worker=request.user.worker, order__status__status='completed')
        context = {
            'available_orders': available_orders,
            'delivered_orders': delivered_orders,
            'completed_orders': completed_orders,
            'is_worker': True,
        }
        return render(request, 'show_order.html', context)
    else:
        return JsonResponse({'message' : 'only worker could access this resource!'}, status=400)

@login_required
def show_order_customer(request):
    if get_user_role(request.user) != 'Customer':
        return JsonResponse({'message' : 'only customer could access this resource!'}, status=400)
    orders = Order.objects.filter(cart__customer=request.user.customer).select_related('status')
    not_paid_orders = orders.filter(status__status='not paid')
    paid_orders = orders.filter(status__status='paid')
    prepared_orders = orders.filter(status__status='prepared')
    ready_orders = orders.filter(status__status='ready')
    delivered_orders = orders.filter(status__status='delivered')
    completed_orders = orders.filter(status__status='completed')
    reviewed_orders = orders.filter(status__status='reviewed')
    cancelled_orders = orders.filter(status__status='cancelled')
    context = {
        'not_paid_orders': not_paid_orders,
        'paid_orders': paid_orders,
        'prepared_orders': prepared_orders,
        'ready_orders': ready_orders,
        'delivered_orders': delivered_orders,
        'completed_orders': completed_orders,
        'reviewed_orders': reviewed_orders,
        'cancelled_orders': cancelled_orders,
        'is_customer': True
    }
    return render(request, 'show_order.html', context)

@login_required
def order_detail(request, id):
    order = Order.objects.get(pk=id)
    product_carts = ProductCart.objects.filter(cart=order.cart)

    role = get_user_role(request.user)
    if role == 'Customer':
        if order.cart.customer != request.user.customer:
            return JsonResponse({'message': 'you are not belong to this order'}, status=400)
    elif role == 'Worker':
        try:
            worker = OrderPayment.objects.get(order=order).worker
            if worker != request.user.worker:
                return JsonResponse({'message': 'you are not belong to this order'}, status=400)
        except OrderPayment.DoesNotExist:
            return JsonResponse({'message': 'you are not belong this order'}, status=400)

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
        ] and get_user_role(request.user) == 'Customer'
    }
    if get_user_role(request.user) == 'Worker':
        context['is_worker'] = True
    elif get_user_role(request.user) == 'Customer':
        context['is_customer'] = True
    elif get_user_role(request.user) == 'Admin':
        context['is_admin'] = True
    return render(request, 'show_order_details.html', context)

@login_required
@permission_required('order.set_to_cancelled')
def cancel_order(request, id):
    order = get_object_or_404(Order, id=id)
        
    if order.cart.customer != request.user.customer:
        return JsonResponse({'message' :'You don\'t have permission to cancel this order.' }, status=400)
    
    cancellable_statuses = [
        'not paid',
        'paid',
    ]
    
    if order.status.status not in cancellable_statuses:
        return JsonResponse({'message' :'You don\'t have permission to cancel this order.' }, status=400)

    if order.status.id == uuid.UUID(PAID_STATUS_ID):
        update_product(order.cart)
        wallet = Wallet.objects.get(walletAccount__user = request.user)
        update_wallet_ballance(wallet, wallet.saldo + order.total)

    cancelled_status = OrderStatus.objects.get(id='88888888888888888888888888888888')
    order.status = cancelled_status
    order.save()
    
    messages.success(request, "Your order has been cancelled successfully.")
    return redirect('order:order_detail', id=id)
