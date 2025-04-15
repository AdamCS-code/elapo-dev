from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import AdminActivityLog
from main.models import Admin

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
    
    return render(request, 'admin-panel/dashboard.html', {
        'total_users': total_users,
        'users': users,
        'admin_user_ids': admin_user_ids,
        'customer_user_ids': customer_user_ids,
        'worker_user_ids': worker_user_ids,
    })


@login_required
def delete_user(request, user_id):
    # Check if the current user is an admin
    try:
        admin = Admin.objects.get(user=request.user)
        # User is an admin, proceed with deletion
    except Admin.DoesNotExist:
        # User is not an admin, redirect to no permission page
        return redirect('no_permission')

    user_to_delete = get_object_or_404(User, id=user_id)

    # Log the admin activity
    AdminActivityLog.objects.create(
        admin=admin,
        action=f"Deleted user: {user_to_delete.username}"
    )

    user_to_delete.delete()
    return redirect('dashboard')


def no_permission(request):
    return render(request, 'admin-panel/no_permission.html', status=403)

