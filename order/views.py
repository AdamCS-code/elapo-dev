from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
import json, uuid

@login_required
def show_order(request):
    return render(request, 'show_order.html', context={})

@login_required
def view_order(request):
    return JsonResponse