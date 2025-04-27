from django.shortcuts import render, get_object_or_404, redirect
from order.models import Order, OrderStatus
import uuid
from .forms import FraudReportForm, ReviewForm
from .models import FraudReport, Review
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from core.views import get_user_role
from django.http import JsonResponse
from django.utils.html import escape


# ===========================
# CREATE Fraud Report
# ===========================
@login_required
def create_fraud_report(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if request.method == "POST":
        form = FraudReportForm(request.POST)
        if form.is_valid():
            description = form.cleaned_data['description']
            sanitized_description = escape(description)

            fraud_report = form.save(commit=False)
            fraud_report.report_id = uuid.uuid4()
            fraud_report.user = request.user
            fraud_report.order = order
            fraud_report.description = sanitized_description
            fraud_report.save()
            messages.success(request, "Fraud Report berhasil dikirim!")
            return redirect("order:order_detail", id=order_id)
        else:
            messages.error(request, "Terjadi kesalahan dalam pengisian formulir.")
    else:
        form = FraudReportForm()

    return render(request, "create_report.html", {"form": form})

# ===========================
# EDIT Report
# ===========================
@login_required
def update_fraud_report(request, report_id):
    report = get_object_or_404(FraudReport, pk=report_id)

    # Pastikan hanya user yang membuat testimoni yang bisa mengedit
    if report.user != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk mengedit report ini.")
        return redirect('main:home')
    
    if request.method == "POST":
        form = FraudReportForm(request.POST, instance=report)
        if form.is_valid():
            description = form.cleaned_data['description']
            sanitized_description = escape(description)

            report = form.save(commit=False)
            report.description = sanitized_description
            report.save()
            messages.success(request, "Report berhasil diperbarui!")
            return redirect('main:home')
        else:
            messages.error(request, "Terjadi kesalahan dalam pengisian formulir.")
    else:
        form = FraudReportForm(instance=report)
    
    return render(request, "edit_report.html", {"form": form, "report": report})

# ===========================
# DELETE Report
# ===========================
@login_required
def delete_fraud_report(request, report_id):
    report = get_object_or_404(FraudReport, pk=report_id)
    report.delete()
    messages.success(request, "Report berhasil dihapus.")
    return redirect("main:home")

# ===========================
# GET Report for User (Customer)
# ===========================
@login_required
def get_report(request):
    context = {'user': request.user}
    if get_user_role(request.user) == 'Customer':
        context['is_customer'] = True
    else:
        return JsonResponse({'message': 'hmm you cannot see this, your not customer'})

    reports = FraudReport.objects.filter(user=request.user)
    context['reports'] = reports
    return render(request, 'user_report.html', context)


# ===========================
# CREATE Review
# ===========================
@login_required
def create_review(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            description = form.cleaned_data['description']
            sanitized_description = escape(description)

            review = form.save(commit=False)
            review.review_id = uuid.uuid4()
            review.user = request.user
            review.order = order
            review.description = sanitized_description
            review.save()
            order.status = OrderStatus.objects.filter(status='reviewed').first()
            order.save()
            return redirect("main:home")
        else:
            messages.error(request, "Terjadi kesalahan dalam pengisian formulir.")
    else:
        form = ReviewForm()

    return render(request, "create_review_form.html", {"form": form})


@login_required
def get_review(request):
    context = {'user': request.user}
    if get_user_role(request.user) == 'Customer':
        context['is_customer'] = True
    else:
        return JsonResponse({'message': 'hmm you cannot see this, your not customer'})

    reviews = Review.objects.filter(user=request.user)
    context['reviews'] = reviews
    return render(request, 'user_review.html', context)

# ===========================
# EDIT Report
# ===========================
@login_required
def update_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)

    if review.user != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk mengedit report ini.")
        return redirect('main:home')
    
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            description = form.cleaned_data['description']
            sanitized_description = escape(description)

            review = form.save(commit=False)
            review.description = sanitized_description
            review.save()
            messages.success(request, "Review berhasil diperbarui!")
            return redirect("main:home")
        else:
            messages.error(request, "Terjadi kesalahan dalam pengisian formulir.")
    else:
        form = ReviewForm(instance=review)
    return render(request, 'edit_review.html', {'form': form})

# ===========================
# DELETE Review
# ===========================
@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    review.delete()
    messages.success(request, "Review berhasil dihapus.")
    return redirect("main:home")
