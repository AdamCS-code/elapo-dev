from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from .models import AdminActivityLog
from .forms import ProductForm 
from main.models import Admin
from order.models import Order, OrderStatus
from product.views import get_product 
from product.models import Product
from django.http import JsonResponse
from django.shortcuts import redirect
from main.models import Admin

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        try:
            Admin.objects.get(user=request.user)
            # User is an admin, allow
            return view_func(request, *args, **kwargs)
        except Admin.DoesNotExist:
            # User is NOT an admin
            return redirect('administrator:no_permission')
    return _wrapped_view

@login_required
def dashboard(request):
    users = User.objects.all().order_by('-date_joined')
    total_users = users.count()
    
    # Get list of admin user IDs
    admin_users = Admin.objects.all()
    admin_user_ids = [admin.user.id for admin in admin_users]
    
    # Get customer and worker data
    # Assuming you have models for Customer and Worker too
    from main.models import Customer, Worker  # Add appropriate imports
    
    customers = Customer.objects.all()
    workers = Worker.objects.all()
    
    customer_user_ids = [customer.user.id for customer in customers]
    worker_user_ids = [worker.user.id for worker in workers]
    
    return render(request, 'dashboard.html', {
        'total_users': total_users,
        'users': users,
        'admin_user_ids': admin_user_ids,
        'customer_user_ids': customer_user_ids,
        'worker_user_ids': worker_user_ids,
        'is_admin': True,
    })


@login_required
@admin_required
def delete_user(request, user_id):
    # Check if the current user is an admin
    try:
        admin = Admin.objects.get(user=request.user)
        # User is an admin, proceed with deletion
    except Admin.DoesNotExist:
        # User is not an admin, redirect to no permission page
        return redirect('administrator:no_permission')

    user_to_delete = get_object_or_404(User, id=user_id)

    # Log the admin activity
    AdminActivityLog.objects.create(
        admin=admin,
        action=f"Deleted user: {user_to_delete.username}"
    )

    user_to_delete.delete()
    return redirect('administrator:dashboard')


def no_permission(request):
    return render(request, 'no_permission.html', status=403)

@login_required
@admin_required
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('administrator:product_dashboard')
    else:
        form = ProductForm()
    return render(request, 'create_product.html', {'form': form})

@login_required
def product_dashboard(request):
    # Ambil semua produk yang ada di database
    products = Product.objects.all().order_by('-id')  # Mengurutkan berdasarkan ID atau preferensi lainnya
    
    return render(request, 'product_dashboard.html', {'products': products, 'is_admin': True})

@login_required
@admin_required
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('administrator:product_dashboard')
    else:
        form = ProductForm(instance=product)

    return render(request, 'update_product.html', {'form': form})

@login_required
@require_POST
@admin_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('administrator:product_dashboard')


@login_required
def all_product(request):
    products = Product.objects.all() 
    product_json = [
        {
            'id' : product.id,
            'product_name': product.product_name,
            'stock': product.stock,
            'price': float(product.price),
            'description': product.description,
        } for product in products
    ]
     
    return JsonResponse(data={'products' : product_json})

@login_required
@admin_required
def process_order(request, order_id):
    order = Order.objects.get(pk=order_id)
    order.status = OrderStatus.objects.filter(status='ready').first()
    order.save()
    return redirect("order:order_detail", id=order_id)
