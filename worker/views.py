from django.shortcuts import render, redirect
from wallet.models import OrderPayment, Wallet, WalletAccount
from order.models import Order, OrderStatus
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from main.models import Worker
from django.contrib import messages
from django.db import transaction

def worker_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            next_url = request.path
            login_url = f"/login/?next={next_url}"
            return redirect(login_url)
        
        try:
            # check if the user is linked to a Worker profile
            worker = Worker.objects.get(user=request.user)
        except Worker.DoesNotExist:
            return redirect("main:login")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@worker_required
def complete_order(request, id):
    if request.method == 'POST':
        order = Order.objects.get(pk=id)

        if order.status.status != 'delivered':
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


@worker_required
def take_order_status(request, pk):
    order_id = pk
    
    try:
        order = Order.objects.get(id=order_id)
        orderPayment = OrderPayment.objects.get(order=order)
    except Order.DoesNotExist:
        return HttpResponseForbidden("Order not found")
    except OrderPayment.DoesNotExist:
        return HttpResponseForbidden("Order not found")

    if request.method == "POST":
        worker_user = request.user

        try:
            worker = Worker.objects.get(user=worker_user)
        except Worker.DoesNotExist:
            return HttpResponseForbidden("You are not linked to a worker profile")

        action = request.POST.get("action")
        
        if action == "take":
            try:
                with transaction.atomic():
                    order = Order.objects.get(id=order_id)
                    orderPayment = OrderPayment.objects.get(order=order)
                    print(orderPayment.worker)

                    if orderPayment.worker is not None:
                        messages.error(request, "This order has already been taken by someone else.")
                        return redirect("main:home")
                    orderPayment.worker = worker
                    order.status = OrderStatus.objects.filter(status='delivered').first()
                    worker.available = False

                    order.save()
                    orderPayment.save()
                    worker.save()

                    print(orderPayment.worker)

                    messages.success(request, "Order successfully taken.")
                    return redirect("order:order_detail", id=order_id)
                
            except Order.DoesNotExist:
                messages.error(request, "Order not found")
                return redirect("main:home")


        elif action == "decline":
            messages.error(request, "Declined")
            return redirect("main:home")

    elif request.method == "GET":
        order = Order.objects.get(id=order_id)
        customer = order.cart.customer
        context = {
            "order_id": order_id,
            "customer": customer
        }
        return render(request, "take_order_form.html", context=context)       

@worker_required
def complete_order_status(request, pk):
    if request.method == "POST":
        print("POST")
        user = request.user
        order_id = pk

        worker = Worker.objects.get(user=user)

        try:
            order = Order.objects.get(id=order_id)
            orderPayment = OrderPayment.objects.get(order=order)
        except Order.DoesNotExist:
            messages.error(request, "Order not found")
            return redirect("main:home")
        except OrderPayment.DoesNotExist:
            messages.error(request, "Order not found")
            return redirect("main:home")

        if orderPayment.worker.user_id == worker.user_id:
            completed_status = OrderStatus.objects.get(status='completed')
            order.status = completed_status  
            worker.available = True
            order.save()
            worker.save()  
            return redirect("worker:order_complete_page")
        else:
            print("NOT COMPLETED")
            return HttpResponseForbidden("You are not authorized to complete this order")
    
    else:
        messages.error(request, "Invalid request method")
        return redirect("main:home")


def order_complete_page(request):
    return render(request, "order_complete.html")



@worker_required
def worker_homepage(request):
    # Get available orders that are not taken by any worker
    orderPayment = OrderPayment.objects.all()
    available_orders = []
    for order in orderPayment:
        if not order.worker:
            # available
            available_orders.append(order.order)


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
