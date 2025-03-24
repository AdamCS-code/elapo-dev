from django.shortcuts import render
from django.contrib.auth.models import User

def dashboard(request):
    total_users = User.objects.count()
    return render(request, 'admin_panel/dashboard.html', {'total_users': total_users})
