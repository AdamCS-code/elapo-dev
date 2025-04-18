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

@login_required
# permission required 
def create_fraud_report(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == "POST":
        form = FraudReportForm(request.POST)
        if form.is_valid():
            fraud_report = form.save(commit=False)
            fraud_report.report_id = uuid.uuid4()
            fraud_report.customer = request.user.customer
            fraud_report.order = order
            fraud_report.save()

            return redirect("order:order_detail", id=order_id)
    else:
        form = FraudReportForm()

    return render(request, "create_report.html", {"form": form})


@login_required
def update_fraud_report(request, report_id):
    report = get_object_or_404(FraudReport, pk=report_id)
    if request.method == "POST":
        form = FraudReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            redirect("main:home")
        else:
            messages.error(request, "Terjadi kesalahan dalam pengisian formulir.")
    else:
        form = FraudReportForm(instance=report)
    
    return render(request, "edit_report.html", {"form": form, "report": report})

@login_required
def delete_fraud_report(request, report_id):
    report = get_object_or_404(FraudReport, pk=report_id)
    report.delete()
    messages.success(request, "Report berhasil dihapus.")
    return redirect("main:home")

@login_required
def create_review(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.review_id = uuid.uuid4()
            review.customer = request.user.customer
            review.order = order
            review.save()
            order.status = OrderStatus.objects.filter(status='reviewed').first()
            order.save()
            return redirect("main:home")
    else:
        form = ReviewForm()

    return render(request, "create_review_form.html", {"form": form})

@login_required
def get_report(request):
    context = {'user': request.user}
    if get_user_role(request.user) == 'Customer':
        context['is_customer'] = True
    else:
        return JsonResponse({'message': 'hmm you cannot see this, your not customer'})

    reports = FraudReport.objects.filter(customer=request.user.customer)
    context['reports'] = reports
    return render(request, 'user_report.html', context)

@login_required
def get_review(request):
    context = {'user': request.user}
    if get_user_role(request.user) == 'Customer':
        context['is_customer'] = True
    else:
        return JsonResponse({'message': 'hmm you cannot see this, your not customer'})

    reviews = Review.objects.filter(customer=request.user.customer)
    context['reviews'] = reviews
    return render(request, 'user_review.html', context)

@login_required
def update_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            redirect("main:home")
        else:
            messages.error(request, "Terjadi kesalahan dalam pengisian formulir.")
    else:
        form = ReviewForm(instance=review)
    return render(request, 'edit_review.html', {'form': form})

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    review.delete()
    messages.success(request, "Review berhasil dihapus.")
    return redirect("main:home")
