from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.html import escape
from .models import Testimony
from product.models import Product
from .forms import TestimonyForm
import uuid
from django.http import JsonResponse
from core.views import get_user_role


# ===========================
# CREATE Testimony
# ===========================
@login_required
def create_testimony(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        form = TestimonyForm(request.POST)
        if form.is_valid():
            # Sanitasi input untuk menghindari XSS
            message = form.cleaned_data['message']
            sanitized_message = escape(message)  # Sanitasi input

            testimony = form.save(commit=False)
            testimony.testimony_id = uuid.uuid4()
            testimony.user = request.user
            testimony.product = product
            testimony.message = sanitized_message  # Input yang sudah disanitasi
            testimony.save()
            messages.success(request, "Testimoni berhasil dikirim!")
            return redirect('main:home')
        else:
            messages.error(request, "Terjadi kesalahan dalam pengisian formulir.")
    else:
        form = TestimonyForm()

    return render(request, "create_testimoni.html", {"form": form, "product": product})


# ===========================
# EDIT Testimony
# ===========================
@login_required
def edit_testimony(request, testimony_id):
    testimony = get_object_or_404(Testimony, pk=testimony_id)

    # Pastikan hanya user yang membuat testimoni yang bisa mengedit
    if testimony.user != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk mengedit testimoni ini.")
        return redirect('main:home')

    if request.method == 'POST':
        form = TestimonyForm(request.POST, instance=testimony)
        if form.is_valid():
            # Sanitasi input
            message = form.cleaned_data['message']
            sanitized_message = escape(message)

            testimony = form.save(commit=False)
            testimony.message = sanitized_message  # Input yang sudah disanitasi
            testimony.save()
            messages.success(request, "Testimoni berhasil diperbarui!")
            return redirect('main:home')
        else:
            messages.error(request, "Terjadi kesalahan dalam pengisian formulir.")
    else:
        form = TestimonyForm(instance=testimony)

    return render(request, "edit_testimoni.html", {"form": form, "testimoni": testimony})


# ===========================
# DELETE Testimony
# ===========================
@login_required
def delete_testimony(request, testimony_id):
    testimony = get_object_or_404(Testimony, pk=testimony_id)

    # Pastikan hanya user yang membuat testimoni yang bisa menghapus
    if testimony.user != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk menghapus testimoni ini.")
        return redirect('main:home')

    testimony.delete()
    messages.success(request, "Testimoni berhasil dihapus.")
    return redirect('main:home')


# ===========================
# GET Testimony for User (Customer)
# ===========================
@login_required
def get_testimony(request):
    context = {'user': request.user}
    
    # Cek apakah user adalah customer
    if get_user_role(request.user) == 'Customer':
        context['is_customer'] = True
    else:
        return JsonResponse({'message': 'Anda tidak bisa melihat testimoni karena bukan customer.'})

    # Ambil testimoninya berdasarkan user customer
    testimony = Testimony.objects.filter(user=request.user)
    context['testimoni'] = testimony
    return render(request, 'user_testimoni.html', context)


# ===========================
# GET ALL Testimony for Product
# ===========================
def get_all_testimonies_for_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    testimonies = Testimony.objects.filter(product=product)
    return render(request, 'product_testimonies.html', {'product': product, 'testimonies': testimonies})
