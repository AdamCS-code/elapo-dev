from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import WalletAccount, Wallet, WalletSession, OrderPayment
from .forms import WalletAccountForm, WalletForm, LoginWalletForm, TopUpForm, PaymentForm
from order.models import Order, OrderStatus
from cart.models import ProductCart, Cart
from product.models import Product
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import uuid

stack = list()
NOT_PAID_STATUS_ID = '11111111111111111111111111111111'
PAID_STATUS_ID = '22222222222222222222222222222222'
PREPARED_STATUS_ID = '33333333333333333333333333333333'
READY_STATUS_ID = '44444444444444444444444444444444'
DELIVERED_STATUS_ID = '55555555555555555555555555555555'
COMPLETED_STATUS_ID = '66666666666666666666666666666666'
REVIEWED_STATUS_ID = '77777777777777777777777777777777'
CANCELLED_STATUS_ID = '88888888888888888888888888888888'

def get_user_role(user):
    user_group = user.groups.values_list('name', flat='True')
    if len(user_group) == 1:
        if user_group[0] == 'Admin':
            return 'Admin'
        elif user_group[0] == 'Customer':
            return 'Customer'
        else:
            return 'Worker'
    else:
        return 'hey you mfs'


def update_wallet_balance(wallet, amount):
    wallet.saldo = amount
    wallet.save()

def update_product(cart):
    product_carts = ProductCart.objects.filter(cart=cart)
    for product_cart in product_carts:
        product_cart.product.stock -= product_cart.quantity
        product_cart.product.save()

def update_order_status(order, to_status):
    to_status = OrderStatus.objects.get(pk=to_status)
    order.status = to_status
    order.save()

def order_detail(id):
    try:
        order = Order.objects.get(pk=id)
        product_carts = ProductCart.objects.filter(cart=order.cart)

        product_carts_json = [
            {
                'product' : {
                    'product_id': product_cart.product.id,
                    'product_name': product_cart.product.product_name,
                    'product_stock': product_cart.product.stock,
                    'product_price': product_cart.product.price,
                    'product_description': product_cart.product.description
                },
                'id': product_cart.id,
                'quantity': product_cart.quantity,
            } for product_cart in product_carts
        ]
        context = {
            'order': order,
            'cart_products': product_carts_json,
            'can_cancel': str(order.status.status) in [
                'not paid',
                'paid',
            ]
        }
        return context
    except:
        return None

@login_required
def show_payment(request, id):
    if (get_user_role(request.user) != 'Customer'):
        return JsonResponse({'message' : 'only customer could access this resource!'}, status=400)

    customer = request.user.customer
    context = order_detail(id)
    if not context:
        return JsonResponse({'message': 'fail because order not found'}, status=400)
    return render(request, 'payment_order.html', context) 

@csrf_exempt
@login_required
def pay_order(request, id):
    if (get_user_role(request.user) != 'Customer'):
        return JsonResponse({'message' : 'only customer could access this resource!'}, status=400)

    customer = request.user.customer
    try:
        order = Order.objects.get(pk=id)
    except:
        return JsonResponse({'message': 'order is not exist'}, status=400)
    walletAccount = WalletAccount.objects.get(user=request.user)
    wallet = Wallet.objects.get(walletAccount=walletAccount)
    if order.status.id == uuid.UUID(PAID_STATUS_ID):
        return JsonResponse({'message': 'Already paid'}, status=400)

    # check apakah sudah terautentikasi
    try:
        walletSessionId = request.session['walletSession']
    except KeyError:
        walletSessionId = ''

    if check_wallet_session(walletSessionId) != walletAccount:
        # login dulu, kembalikan ke halaman ini 
        stack.append(('wallet:payment_order', id))
        redirect('wallet:login_wallet')
    
    if order.cart.customer != customer:
        return JsonResponse({'message': 'fail because you are not the one who order it, sorry'}, status=400)
        
    orderPayment, _ = OrderPayment.objects.get_or_create(order=order, walletAccount=walletAccount)
    if request.method == 'POST':
        form = PaymentForm(request.POST)

        if form.is_valid():
            pin = form.cleaned_data['pin']

            walletAccount.reset_attempts_if_needed()

            if walletAccount.login_attempts > 3:
                return JsonResponse({'message': 'you don\'t any attempt left, wait 10 minutes'}, status=400)

            if walletAccount.check_pin(pin):
                # check apakah uang pengguna cukup
                if order.total > wallet.saldo:
                    return JsonResponse({'message': 'fail because you don\'t have enough balance'}, status=400)
                else:
                    update_wallet_balance(wallet, wallet.saldo - order.total)
                    update_product(order.cart)
                    update_order_status(order, PAID_STATUS_ID)
                    print('updated loh')
                    return redirect('order:order_detail', id=order.id)

        else:
            return JsonResponse({'message': 'you entered wrong password'}, status=400)
    else:
        form = PaymentForm()
        form = render_to_string('form_wallet.html', {'form': form}, request)
    return render(request, 'payment_order.html', context={'form': form, 'order': order, 'is_customer': True})


@csrf_exempt
@login_required
def register_wallet(request):
    walletAccount = WalletAccount.objects.filter(user=request.user)
    if walletAccount:
        return redirect('wallet:show_wallet')

    if request.method == 'POST':
        form = WalletAccountForm(request.POST)
        if form.is_valid():
            wallet_account = form.save(commit=False)
            wallet_account.user = request.user
            wallet_account.save()
            wallet = Wallet.objects.create(
                id=uuid.uuid4(),
                walletAccount=wallet_account,
                saldo=0
            )
            return redirect('wallet:show_wallet')  # redirect to wherever you want
    else:
        form = WalletAccountForm()
    form = render_to_string('form_wallet.html', {'form': form}, request=request) 
    try:
        request.user.customer
        is_customer = True
    except:
        is_customer = False

    return render(request, 'show_wallet.html', {'form': form, 'is_customer': is_customer})

@csrf_exempt
@login_required
def topup_wallet(request):
    walletAccount = check_wallet_session(request.session['walletSession'])

    if not walletAccount:
        return redirect('wallet:login_wallet')
    
    wallet_account = get_object_or_404(WalletAccount, user=request.user)
    wallet = wallet_account.wallet

    if request.method == 'POST':
        form = TopUpForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']

            update_wallet_balance(wallet, wallet.saldo + amount)
            return redirect('wallet:show_wallet')
    else:
        form = TopUpForm()

    form = render_to_string('form_wallet.html', {'form': form}, request=request)
    try:
        request.user.customer
        is_customer = True
    except:
        is_customer = False
    return render(request, 'show_wallet.html', {'form': form, 'is_customer': is_customer})

@login_required
@csrf_exempt
def login_wallet(request):
    try:
        if check_wallet_session(request.session['walletSession']):
            return redirect('wallet:show_wallet')
    except:
        request.session['walletSession'] = ''
     # check if walletAccount is available
    wallet_account = WalletAccount.objects.filter(user_id=request.user.id)
    if (len(wallet_account) == 0):
        return redirect('wallet:register_wallet')

    MAX_ATTEMPTS = 3
    wallet_account = get_object_or_404(WalletAccount, user=request.user)
    
    if wallet_account.login_attempts >= MAX_ATTEMPTS:
        wallet_account.reset_attempts_if_needed()
        return render(request, 'locked.html')

    if request.method == 'POST':
        form = LoginWalletForm(request.POST, wallet_account=wallet_account)
        if form.is_valid():
            wallet_account.login_attempts = 0
            wallet_account.save()
            # create session
            wallet_session = WalletSession.objects.filter(walletAccount__user=request.user)
            if len(wallet_session) > 0:
                wallet_session[0].delete()
            wallet_session = WalletSession.objects.create(walletAccount=wallet_account)
            wallet_session.save()
            request.session['walletSession'] = str(wallet_session.id)
            if len(stack) > 0:
                url = stack.pop()
                redirect(url[0], id=url[1])
                
            return redirect('wallet:show_wallet')
        else:
            wallet_account.login_attempts += 1
            wallet_account.save()
    else:
        form = LoginWalletForm(wallet_account=wallet_account)

    context = {'form': form}


    form = render_to_string('form_wallet.html', context, request=request)
    context = {
        'form': form,
        'attempts_left': MAX_ATTEMPTS - wallet_account.login_attempts,

    }
    user_role = get_user_role(request.user)
    if user_role == 'Admin':
        context['is_admin'] = True
    elif user_role == 'Customer':
        context['is_customer'] = True
    elif user_role == 'Worker':
        context['is_worker'] = True

    return render(request, "show_wallet.html", context)

@login_required
def wallet_dashboard(request):
    walletSession = check_wallet_session(request.session.get('walletSession'))
    if not walletSession:
        request.session['walletSession'] = ''
        return redirect('wallet:login_wallet')

    wallet_account = get_object_or_404(WalletAccount, user=request.user)
    wallet = get_object_or_404(Wallet, walletAccount=wallet_account)
    if get_user_role(request.user) == 'Customer':
        unpaid_orders = Order.objects.filter(cart__customer=request.user.customer, status__id = NOT_PAID_STATUS_ID).order_by('created_at')
        paid_orders = OrderPayment.objects.filter(order__cart__customer=request.user.customer).order_by('created_at')
        context = {
            'payment_history': paid_orders,
            'pending_orders': unpaid_orders,
            'balance': wallet.saldo,
            'wallet_account': wallet_account,
            'is_customer': True,
        }
    elif get_user_role(request.user) == 'Worker':
        context = {
            'balance': wallet.saldo,
            'wallet_account': wallet_account,
            'is_worker': True,
        }
    elif get_user_role(request.user) == 'Admin':
        context = {
            'balance': wallet.saldo,
            'wallet_account': wallet_account,
            'is_admin': True,
        }
    return render(request, 'show_wallet.html', context)

def check_wallet_session(sessionId):
    try:
        wallet = WalletSession.objects.get(id=uuid.UUID(sessionId))
        if not wallet.is_expired():
            return wallet
        else:
            wallet.delete()
            return None

    except WalletSession.DoesNotExist:
        return None
    except KeyError:
        return None
    except:
        return None
