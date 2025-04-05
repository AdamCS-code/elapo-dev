from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core import serializers
from .forms import AdminRegistrationForm, CustomerRegistrationForm, WorkerRegistrationForm, LoginForm

@login_required(login_url='/login')
def show_main_page(request):
    context = {}
    return render(request, 'home.html', context={'user': request.user})

def show_loggedin_page(request):
    return render(request, 'home.html', context={'user': request.user})

@csrf_exempt
def admin_register(request):
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Admin berhasil ditambahkan, silahkan login ya')
            return redirect('main:login')
        else:
            messages.error(request, 'Terjadi Kesalahan. Silahkan coba lagi nanti.')
    else:
        form = AdminRegistrationForm()
    return render(request, 'admin_register.html', {'form': form})

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

    context = {'form': form}
    return render(request, 'customer_register.html', context)


@csrf_exempt
def worker_register(request):
    if request.method == 'POST':
        form = WorkerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Worker berhasil ditambahkan, silahkan login ya')
            return redirect('main:login')
        else:
            messages.error(request, 'Terjadi Kesalahan. Silahkan coba lagi nanti.')
    else:
        form = WorkerRegistrationForm()
    
    context = {'form': form}
    return render(request, 'worker_register.html', context)

def logout_user(request):
    logout(request)
    return redirect('main:home')
