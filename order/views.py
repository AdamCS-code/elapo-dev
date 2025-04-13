from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from main.models import Customer
from .models import Order, OrderStatus
import json, uuid

@login_required
def show_order(request):
    return render(request, 'show_order.html', context={})

@login_required
@permission_required("order.view_order")
def customer_view_order(request):
    customer = Customer.objects.filter(user=request.user).first()

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