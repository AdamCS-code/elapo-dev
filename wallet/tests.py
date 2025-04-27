from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from .models import WalletAccount, Wallet, WalletSession
from main.models import Admin, Customer, Worker
from order.models import Order, OrderStatus
from cart.models import Cart
import uuid
from django.utils import timezone
from datetime import timedelta

class WalletTests(TestCase):

    def setUp(self):
        # Create groups
        Group.objects.create(name='Customer')
        Group.objects.create(name='Worker')
        Group.objects.create(name='Admin')

        # Create user
        self.customer_user = User.objects.create_user(username='customer1', password='password123')
        self.customer_user.groups.add(Group.objects.get(name='Customer'))

        self.customer = Customer.objects.create(user=self.customer_user)
        
        # Create WalletAccount and Wallet
        self.wallet_account = WalletAccount.objects.create(user=self.customer_user, pin='1234')
        self.wallet = Wallet.objects.create(walletAccount=self.wallet_account, saldo=1000)
        
        # Create Cart and Order
        self.cart = Cart.objects.create(customer=self.customer)
        self.order_status = OrderStatus.objects.create(id='11111111111111111111111111111111', status='not paid')
        self.order = Order.objects.create(cart=self.cart, status=self.order_status, total=500)

        self.client = Client()

    def login_customer(self):
        self.client.login(username='customer1', password='password123')

    def create_wallet_session(self):
        # simulate user logged into wallet
        session = WalletSession.objects.create(walletAccount=self.wallet_account)
        self.client.session['walletSession'] = str(session.id)
        self.client.session.save()

    # =============== HAPPY PATHS ===============

    def test_authenticated_user_can_login_wallet(self):
        self.login_customer()
        response = self.client.get(reverse('wallet:login_wallet'))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_register_wallet(self):
        # Create another user without wallet
        user2 = User.objects.create_user(username='newuser', password='password123')
        user2.groups.add(Group.objects.get(name='Customer'))
        self.client.login(username='newuser', password='password123')
        response = self.client.post(reverse('wallet:register_wallet'), {'pin': '5678'})
        self.assertEqual(response.status_code, 200)  # redirect after success

    def test_authenticated_user_with_wallet_can_topup(self):
        self.login_customer()

        wallet_session = WalletSession.objects.create(walletAccount=self.wallet_account)

        session = self.client.session
        session['walletSession'] = str(wallet_session.id)
        session.save()

        # 1. Dapatkan halaman yang mengandung csrf_token
        response = self.client.get(reverse('wallet:topup_wallet'))

        # 2. Ambil csrf_token dari cookies
        csrf_token = response.cookies['csrftoken'].value
        response = self.client.post(reverse('wallet:topup_wallet'), {'amount': 500, 'csrfmiddlewaretoken': csrf_token,})


        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('wallet:show_wallet'))

    def test_authenticated_user_with_wallet_can_pay_order(self):
        self.login_customer()

        wallet_session = WalletSession.objects.create(walletAccount=self.wallet_account)

        session = self.client.session
        session['walletSession'] = str(wallet_session.id)
        session.save()
        # 1. Dapatkan halaman yang mengandung csrf_token
        response = self.client.get(reverse('wallet:topup_wallet'))

        # 2. Ambil csrf_token dari cookies
        csrf_token = response.cookies['csrftoken'].value

        response = self.client.post(reverse('wallet:pay_order', args=[self.order.id]), {'pin': '1234', 'csrfmiddlewaretoken': csrf_token,})
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        #self.assertEqual(str(self.order.status.id), '22222222222222222222222222222222')  # paid status
'''
    # =============== UNHAPPY PATHS ===============

    def test_unauthenticated_user_login_wallet_redirects(self):
        response = self.client.get(reverse('wallet:login_wallet'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_authenticated_user_login_wallet_other_wallet_fail(self):
        # Simulate wrong wallet login attempt by tampering session
        self.login_customer()
        self.client.session['walletSession'] = str(uuid.uuid4())
        self.client.session.save()
        response = self.client.get(reverse('wallet:login_wallet'))
        self.assertEqual(response.status_code, 200)  # forced to re-login or register

    def test_authenticated_user_register_wallet_when_already_exists_redirect(self):
        self.login_customer()
        response = self.client.get(reverse('wallet:register_wallet'))
        self.assertEqual(response.status_code, 302)  # redirect to show_wallet

    def test_unauthenticated_user_register_wallet_redirects(self):
        response = self.client.get(reverse('wallet:register_wallet'))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_pay_order_not_exist(self):
        self.login_customer()
        self.create_wallet_session()
        response = self.client.post(reverse('wallet:pay_order', args=[uuid.uuid4()]), {'pin': '1234'})
        self.assertEqual(response.status_code, 404)

    def test_authenticated_user_pay_order_already_paid(self):
        self.login_customer()
        self.create_wallet_session()
        paid_status = OrderStatus.objects.create(id='22222222222222222222222222222222', status='paid')
        self.order.status = paid_status
        self.order.save()

        response = self.client.post(reverse('wallet:pay_order', args=[self.order.id]), {'pin': '1234'})
        self.assertContains(response, 'fail because you are not the one who order it', status_code=400)

    def test_authenticated_user_pay_order_not_own(self):
        # Another customer
        user2 = User.objects.create_user(username='othercustomer', password='password123')
        user2.groups.add(Group.objects.get(name='Customer'))
        cart2 = Cart.objects.create(customer=user2.customer)
        order2 = Order.objects.create(cart=cart2, status=self.order_status, total=500)

        self.login_customer()
        self.create_wallet_session()
        response = self.client.post(reverse('wallet:pay_order', args=[order2.id]), {'pin': '1234'})
        self.assertContains(response, 'fail because you are not the one who order it', status_code=400)

    # =============== OWASP / SECURITY PATHS ===============

    def test_expired_wallet_session_deleted(self):
        self.login_customer()
        # Create expired session
        expired_session = WalletSession.objects.create(walletAccount=self.wallet_account)
        expired_session.created_at = timezone.now() - timedelta(minutes=20)  # 20 minutes ago
        expired_session.save()

        self.client.session['walletSession'] = str(expired_session.id)
        self.client.session.save()

        # Try to access dashboard with expired session
        response = self.client.get(reverse('wallet:show_wallet'))
        self.assertEqual(response.status_code, 302)  # should be redirected to login_wallet

    def test_wallet_session_restriction_only_owner(self):
        # Log in as other user
        user2 = User.objects.create_user(username='hacker', password='password123')
        user2.groups.add(Group.objects.get(name='Customer'))
        self.client.login(username='hacker', password='password123')

        self.client.session['walletSession'] = str(uuid.uuid4())  # random invalid session
        self.client.session.save()

        response = self.client.get(reverse('wallet:show_wallet'))
        self.assertEqual(response.status_code, 302)
'''
