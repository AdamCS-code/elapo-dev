from django.urls import path
from .views import wallet_dashboard, register_wallet, login_wallet, topup_wallet

app_name='wallet'

urlpatterns = [
    path('', wallet_dashboard, name="show_wallet"),
    path('register-wallet', register_wallet, name="register_wallet"),
    path('login-wallet', login_wallet, name="login_wallet"),
    path('topup-wallet', topup_wallet, name='topup_wallet'),
    path('pay-order/<str:id>', wallet_dashboard, name='pay_order')
]
