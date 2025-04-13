from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import WalletAccount, Wallet, WalletSession
from .forms import WalletAccountForm, WalletForm, LoginWalletForm, TopUpForm
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import uuid

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
    return render(request, 'show_wallet.html', {'form': form})

@login_required
def topup_wallet(request):
    walletAccount = check_wallet_session(request.session['walletSession'])

    if not walletAccount:
        return redirect('wallet:login_wallet')
    
    wallet_account = get_object_or_404(WalletAccount, user=request.user)
    if request.method == 'POST':
        form = TopUpForm(request.POST)
        if form.is_valid():
            wallet = wallet_account.wallet
            amount = form.cleaned_data['amount']
            wallet.saldo += amount
            wallet.save()
            return redirect('wallet:show_wallet')
    else:
        form = TopUpForm()

    form = render_to_string('form_wallet.html', {'form': form}, request=request)
    return render(request, 'show_wallet.html', {'form': form})

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
            wallet_session = WalletSession.objects.create(id=uuid.uuid4(),walletAccount=wallet_account)
            wallet_session.save()
            request.session['walletSession'] = str(wallet_session.id)
            return redirect('wallet:show_wallet')
        else:
            wallet_account.login_attempts += 1
            wallet_account.save()
    else:
        form = LoginWalletForm(wallet_account=wallet_account)
    form = render_to_string('form_wallet.html', {'form': form}, request=request)
    return render(request, "show_wallet.html", {
        'form': form,
        'attempts_left': MAX_ATTEMPTS - wallet_account.login_attempts
    })

@login_required
def wallet_dashboard(request):
    walletSession = check_wallet_session(request.session.get('walletSession'))
    if not walletSession:
        return redirect('wallet:login_wallet')

    wallet_account = get_object_or_404(WalletAccount, user=request.user)
    wallet = get_object_or_404(Wallet, walletAccount=wallet_account)

    context = {
        'balance': wallet.saldo,
        'wallet_account': wallet_account,
    }
    return render(request, 'show_wallet.html', context)

def check_wallet_session(sessionId):
    print(sessionId)
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
