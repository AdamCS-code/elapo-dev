from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse

from main.models import Worker
from worker.views import worker_required
from .forms import AdminRegistrationForm, CustomerRegistrationForm, WorkerEditForm, WorkerRegistrationForm, LoginForm
from django.template.loader import render_to_string
from django.db import IntegrityError
from order.models import Order, OrderStatus


@login_required(login_url='/login')
def show_main_page(request): 
    context = {'user': request.user}
    try:
        customer = request.user.customer
        context = {
            'customer': request.user.customer,
            'is_customer': True
        }
    except:
        print('not customer')
    try:
        worker = request.user.worker
        available_orders = Order.objects.filter(worker__isnull=True)
        print("AVAILABLE ORDERS")
        print(available_orders)

        context = {
            'worker': request.user.worker,
            'is_worker': True,
            'orders': available_orders
        }

    except:
        print('not worker')

    try:
        admin = request.user.admin
        context = {
            'admin': request.user.admin,
            'is_admin': True,
        }
    except:
        print('not admin')

    return render(request, 'home.html', context)


def show_loggedin_page(request):
    return render(request, 'home.html', context={'user': request.user})

def show_register(request):
    return render(request, 'register.html', context={'user': request.user})

@csrf_protect
def login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        try:
            form.clean()
        except Exception as e:
            print(f"Clean method failed: {e}")
        
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, 'Anda berhasil login.')
            return redirect('main:home') 
        else:            
            messages.error(request, 'Email atau password salah. Silakan coba lagi.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

@csrf_exempt
def customer_register(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer berhasil ditambahkan, silahkan login ya')
            return redirect('main:login')
        else:
            messages.error(request, 'Terjadi Kesalahan. Silahkan coba lagi nanti.')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'register_customer.html',{'form': form})

@csrf_exempt
def worker_register(request):
    if request.method == 'POST':
        form = WorkerRegistrationForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Worker berhasil ditambahkan, silahkan login ya')
                return redirect('main:login')
            except IntegrityError:
                messages.error(request, 'Username sudah terdaftar, silakan pilih username lain.')
        else:
            messages.error(request, 'Terjadi Kesalahan. Silahkan coba lagi nanti.')
    else:
        form = WorkerRegistrationForm() 
    return render(request, 'register_worker.html',{'form': form})

def logout_user(request):
    logout(request)
    return redirect('main:home')


@worker_required
def edit_profile_worker(request):
    try:
        worker = Worker.objects.get(user=request.user)
    except Worker.DoesNotExist:
        messages.error(request, "Worker profile not found")
        return redirect('main:home')
    
    if request.method == 'POST':
        form = WorkerEditForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('worker:profile')
    else:
        form = WorkerEditForm(instance=worker)
    
    return render(request, 'edit_profile.html', {'form': form})
