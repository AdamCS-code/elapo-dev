from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from main.models import Admin, Customer, Worker
from worker.views import worker_required
from .forms import AdminRegistrationForm, CustomerEditForm, CustomerRegistrationForm, WorkerEditForm, WorkerRegistrationForm, LoginForm
from django.template.loader import render_to_string
from django.db import IntegrityError
from order.models import Order, OrderStatus
from django.core.cache import cache
from django.http import HttpResponseForbidden
import time

def rate_limit(key_func, rate='5/s', block_time=60):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            key = key_func(request)
            rate_num, rate_period = rate.split('/')
            period = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[rate_period]
            
            history = cache.get(key, [])
            now = time.time()
            
            # Remove old requests
            history = [t for t in history if now - t <= period]
            
            if len(history) >= int(rate_num):
                if block_time:
                    cache.set(key, history, block_time)
                return render(request, "rate_limit_exceeded.html", {"retry_after": block_time})
                
            history.append(now)
            cache.set(key, history, period)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


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
@rate_limit(lambda req: f"login:{req.META['REMOTE_ADDR']}", rate='5/m')
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

def edit_profile_customer(request):
    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        messages.error(request, "Customer profile not found")
        return redirect('main:home')
    
    if request.method == 'POST':
        form = CustomerEditForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('main:home')
    else:
        form = CustomerEditForm(instance=customer)
    
    return render(request, 'edit_profile.html', {'form': form})

def edit_profile_admin(request):
    try:
        admin = request.user.admin
    except Admin.DoesNotExist:
        messages.error(request, "Admin profile not found")
        return redirect('main:home')
    
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST, instance=admin)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('main:home')
    else:
        form = AdminRegistrationForm(instance=admin)
    
    return render(request, 'edit_profile.html', {'form': form})