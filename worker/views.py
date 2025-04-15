from django.shortcuts import render, redirect
from wallet.models import OrderPayment, Wallet, WalletAccount
from order.models import Order, OrderStatus
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from main.models import Worker

def worker_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        try:
            # check if the user is linked to a Worker profile
            worker = Worker.objects.get(user=request.user)
        except Worker.DoesNotExist:
            return HttpResponseForbidden("Not authorized, you must be a worker!")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@worker_required
def complete_order(request, id):
    if request.method == 'POST':
        order = Order.objects.get(pk=id)

        if order.status.id != '55555555555555555555555555555555':
            return JsonResponse({'message': 'cannot complete completed order'})
        orderPayment = OrderPayment.objects.get(order=order)

        if orderPayment.worker != request.user.worker:
            return JsonResponse({'message': 'you can not complete other people work'})

        COMPLETED_STATUS_ID = '66666666666666666666666666666666'
        order.status = OrderStatus.objects.get(pk=COMPLETED_STATUS_ID)
        order.save()

        wallet = Wallet.objects.get(walletAccount__user = request.user)
        wallet.saldo += orderPayment.delivery_fee
        wallet.save()
    return redirect('order:order_detail', id=id)

@login_required
@worker_required
def take_order_status(request, pk):
    order_id = pk
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponseForbidden("Order not found")

    if request.method == "POST":
        worker_user = request.user

        try:
            worker = Worker.objects.get(user=worker_user)
        except Worker.DoesNotExist:
            return HttpResponseForbidden("You are not linked to a worker profile")

        action = request.POST.get("action")

        if action == "take":
            order = OrderPayment.objects.get(order=order)
            order.set_worker(worker)
            order.order.status = OrderStatus.objects.filter(status='delivered').first()
            order.order.save()
            return redirect("order:order_detail", id=order_id)
        
        elif action == "decline":
            return redirect("worker:homepage")

    elif request.method == "GET":
        order = Order.objects.get(order_id=order_id)
        customer = order.customer
        context = {
            "order_id": order_id,
            "customer": customer
        }
        return render(request, "take_order_form.html", context=context)       

@login_required
@worker_required
def complete_order_status(request):
    if request.method == "POST":
        worker = request.user
        order_id = request.POST["order_id"]

        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return HttpResponseForbidden("Order not found")

        if order.worker.user_id == worker.user_id:
            order.status = OrderStatus.objects.filter('completed').first()
            order.status.save()
        else:
            return HttpResponseForbidden("You are not authorized to complete this order")

        order.save()
        return redirect("worker:order-complete-page")
    
    else:
        return HttpResponseForbidden("Invalid request method")
def order_complete_page(request):
    return render(request, "order_complete.html")


@worker_required
def worker_homepage(request):
    # Get available orders that are not taken by any worker
    available_orders = OrderPayment.objects.filter(worker__isnull=True, order__status__status='ready')
    print("AVAILABLE ORDERS")
    print(available_orders)
    context = {"orders": available_orders, 'is_worker': True}
    return render(request, "worker_homepage.html", context=context)

@worker_required
def worker_profile_page(request):
    user = request.user
    worker = Worker.objects.get(user=request.user)
    context = {"worker": worker}
    return render(request, "worker_profile_page.html", context=context)
