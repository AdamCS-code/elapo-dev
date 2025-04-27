from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from main.models import Customer, Worker, Admin
from cart.models import ProductCart, Cart
from order.models import Order, OrderStatus
from product.models import Product
from wallet.models import WalletAccount, Wallet, OrderPayment
from core.views import get_user_role
import uuid
import json
from unittest.mock import patch

class OrderViewsTest(TestCase):
    def setUp(self):
        # Create user groups
        self.admin_group = Group.objects.create(name='Admin')
        self.worker_group = Group.objects.create(name='Worker')
        self.customer_group = Group.objects.create(name='Customer')
        
        # Create user roles
        self.admin_user = User.objects.create_user(username='admin', email='admin@example.com', password='password123')
        self.worker_user = User.objects.create_user(username='worker', email='worker@example.com', password='password123')
        self.customer_user = User.objects.create_user(username='customer', email='customer@example.com', password='password123')
        self.other_customer_user = User.objects.create_user(username='other_customer', email='other@example.com', password='password123')
        
        # Assign users to groups
        self.admin_user.groups.add(self.admin_group)
        self.worker_user.groups.add(self.worker_group)
        self.customer_user.groups.add(self.customer_group)
        self.other_customer_user.groups.add(self.customer_group)

        # dummy product for testing
        self.product = Product.objects.create(product_name='product1', stock=1000, price=10000, description='')

        # Create order statuses
        self.not_paid_status = OrderStatus.objects.create(id=uuid.UUID('11111111111111111111111111111111'), status='not paid')
        self.paid_status = OrderStatus.objects.create(id=uuid.UUID('22222222222222222222222222222222'), status='paid')
        self.prepared_status = OrderStatus.objects.create(id=uuid.UUID('33333333333333333333333333333333'), status='prepared')
        self.ready_status = OrderStatus.objects.create(id=uuid.UUID('44444444444444444444444444444444'), status='ready')
        self.delivered_status = OrderStatus.objects.create(id=uuid.UUID('55555555555555555555555555555555'), status='delivered')
        self.completed_status = OrderStatus.objects.create(id=uuid.UUID('66666666666666666666666666666666'), status='completed')
        self.reviewed_status = OrderStatus.objects.create(id=uuid.UUID('77777777777777777777777777777777'), status='reviewed')
        self.cancelled_status = OrderStatus.objects.create(id=uuid.UUID('88888888888888888888888888888888'), status='cancelled')
        
        # Create customer instances
        self.customer = Customer.objects.create(user=self.customer_user)
        self.other_customer = Customer.objects.create(user=self.other_customer_user)

        self.customer.user.user_permissions.add(Permission.objects.get(codename='set_to_cancelled', content_type__app_label='order'))
        self.other_customer.user.user_permissions.add(Permission.objects.get(codename='set_to_cancelled', content_type__app_label='order'))

        # Create worker instance
        self.worker = Worker.objects.create(user=self.worker_user)
        
        # Create admin instance
        self.admin = Admin.objects.create(user=self.admin_user)

        # Create cart for admin #1 test case 
        self.cart = Cart.objects.create(customer=self.customer)
        self.other_cart = Cart.objects.create(customer=self.other_customer)

        # Create product cart
        self.product_cart = ProductCart.objects.create(cart=self.cart, product=self.product, quantity=10)
        self.other_product_cart = ProductCart.objects.create(cart=self.other_cart, product=self.product, quantity=10)

        # Create order 
        self.order = Order.objects.create(cart=self.cart,total=100000, status=self.not_paid_status)
        self.other_order = Order.objects.create(cart=self.other_cart,total=100000, status=self.not_paid_status)

        # Create wallet account and wallet for customer
        self.customer_wallet_account = WalletAccount.objects.create(user=self.customer.user, pin='111111')
        self.customer_wallet = Wallet.objects.create(walletAccount=self.customer_wallet_account)

        # Create wallet account and wallet for worker
        self.worker_wallet_account = WalletAccount.objects.create(user=self.worker.user, pin='111111')
        self.worker_wallet = Wallet.objects.create(walletAccount=self.worker_wallet_account)

        # Create wallet account and wallet for admin
        self.admin_wallet_account = WalletAccount.objects.create(user=self.admin.user, pin='111111')
        self.admin_wallet = Wallet.objects.create(walletAccount=self.admin_wallet_account)

        # Create clients
        self.admin_client = Client()
        self.admin_client.login(username='admin', password='password123')
        
        self.worker_client = Client()
        self.worker_client.login(username='worker', password='password123')
        
        self.customer_client = Client()
        self.customer_client.force_login(self.customer.user)

        
        self.other_customer_client = Client()
        self.other_customer_client.login(username='other_customer', password='password123')
        
        # Mock for get_user_role function
        self.patcher = patch('core.views.get_user_role')
        self.mock_get_user_role = self.patcher.start()
        
    def tearDown(self):
        self.patcher.stop()

    # OWASP TESTS
    def test_broken_access_control_non_owner_cancel(self):
        """Test broken access control: non-owner trying to cancel order"""
        self.mock_get_user_role.return_value = 'Customer'
        response = self.other_customer_client.post(reverse('order:cancel_order', args=[self.order.id]))
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content,{'message' :'You don\'t have permission to cancel this order.' })
        # Order should not be cancelled
        self.order.refresh_from_db()
        self.assertNotEqual(self.order.status, self.cancelled_status)
    
    def test_unauthorized_order_detail_access(self):
        """Test data integrity: customer trying to view another customer's order details"""
        self.mock_get_user_role.return_value = 'Customer'
        response = self.other_customer_client.get(reverse('order:order_detail', args=[self.order.id]))
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'message': 'you are not belong to this order'})
    
    def test_worker_unauthorized_order_detail_access(self):
        """Test worker trying to access order details where they are not assigned"""
        self.mock_get_user_role.return_value = 'Worker'
        self.order.status = self.ready_status
        self.order.save()
        response = self.worker_client.get(reverse('order:order_detail', args=[self.order.id]))
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'message': 'you are not belong this order'})
    
    def test_sql_injection_in_order_id(self):
        """Test SQL injection in order ID parameter"""
        self.mock_get_user_role.return_value = 'Customer'
        # Trying a simple SQL injection
        response = self.customer_client.get('/order/detail/1 OR 1=1')
        # Django's URL resolver should reject this as a 404
        self.assertEqual(response.status_code, 404)
    
    def test_csrf_protection(self):
        """Test CSRF protection for cancel order"""
        self.mock_get_user_role.return_value = 'Customer'
        client = Client(enforce_csrf_checks=True)
        client.login(username='customer', password='password123')
        
        # Try to cancel order without CSRF token
        response = client.post(reverse('order:cancel_order', args=[self.order.id]))
        # Django should return 403 CSRF verification failed
        self.assertEqual(response.status_code, 403)
        
    def test_server_side_request_forgery(self):
        """Test for SSRF by trying to manipulate request headers"""
        self.mock_get_user_role.return_value = 'Customer'
        # Attempt to manipulate headers
        response = self.customer_client.get(
            reverse('order:order_detail', args=[self.order.id]),
            HTTP_HOST='malicious-site.com',
            HTTP_REFERER='https://malicious-site.com'
        )
        self.assertEqual(response.status_code, 400)
'''
    # UNHAPPY PATH TESTS
    def test_admin_accessing_customer_view(self):
        """Test admin trying to access customer-specific view"""
        self.mock_get_user_role.return_value = 'Admin'
        response = self.admin_client.get(reverse('order:show_order'))
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'message': 'only customer could access this resource!'})
    
    def test_admin_accessing_worker_view(self):
        """Test admin trying to access worker-specific view"""
        self.mock_get_user_role.return_value = 'Admin'
        response = self.admin_client.get(reverse('order:show_order_worker'))
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'message': 'only worker could access this resource!'})
    
    def test_customer_accessing_admin_view(self):
        """Test customer trying to access admin-specific view"""
        self.mock_get_user_role.return_value = 'Customer'
        response = self.customer_client.get(reverse('order:show_order_admin'))
        # This should redirect rather than giving an error response because of the show_order logic
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'message': 'only admin could access this resource!'})
    
    def test_customer_accessing_worker_view(self):
        """Test customer trying to access worker-specific view"""
        self.mock_get_user_role.return_value = 'Customer'
        response = self.customer_client.get(reverse('order:show_order_worker'))
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'message': 'only worker could access this resource!'})
    
    def test_worker_accessing_admin_view(self):
        """Test worker trying to access admin-specific view"""
        self.mock_get_user_role.return_value = 'Worker'
        response = self.worker_client.get(reverse('order:show_order_admin'))
        # This should redirect rather than giving an error response because of the show_order logic
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'message': 'only admin could access this resource!'})
    
    def test_worker_accessing_customer_view(self):
        """Test worker trying to access customer-specific view"""
        self.mock_get_user_role.return_value = 'Worker'
        response = self.worker_client.get(reverse('order:show_order'))
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'message': 'only customer could access this resource!'})
    
    def test_worker_cancel_order(self):
        """Test worker trying to cancel an order (not allowed)"""
        self.mock_get_user_role.return_value = 'Worker'
        response = self.worker_client.post(reverse('order:cancel_order', args=[self.order.id]))
        # Since worker doesn't have the required permission, Django should deny access
        self.assertEqual(response.status_code, 302)

    def test_customer_cancel_other_customer_order(self):
        """Test customer trying to cancel another customer's order"""
        self.mock_get_user_role.return_value = 'Customer'
        response = self.customer_client.post(reverse('order:cancel_order', args=[self.other_order.id]))
        # This should show an error message and redirect
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content,{'message' :'You don\'t have permission to cancel this order.' })
    
    def test_admin_cancel_order(self):
        """Test admin trying to cancel an order (not allowed unless they have permission)"""
        self.mock_get_user_role.return_value = 'Admin'
        response = self.admin_client.post(reverse('order:cancel_order', args=[self.order.id]))
        # Since admin doesn't have the required permission, Django should deny access
        self.assertEqual(response.status_code, 302)
    
    # HAPPY PATH
    def test_customer_cancel_paid_order(self):
        """Test customer cancelling a paid order with refund"""
        
        self.mock_get_user_role.return_value = 'Customer'

        self.order.status = self.paid_status
        self.order.save()

        initial_balance = self.customer_wallet.saldo
        response = self.customer_client.post(reverse('order:cancel_order', args=[self.order.id]))
        self.assertRedirects(response, reverse('order:order_detail', args=[self.order.id]))
        
        # Verify order status has been updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, self.cancelled_status)
        
        # Verify wallet balance has been updated
        self.customer_wallet.refresh_from_db()
        self.assertEqual(self.customer_wallet.saldo, initial_balance + self.order.total)

    def test_admin_show_order_admin(self):
        """Test admin accessing show_order_admin view"""
        self.mock_get_user_role.return_value = 'Admin'
        self.order.status = self.paid_status
        self.order.save()
        response = self.admin_client.get(reverse('order:show_order_admin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_order_admin.html')
        self.assertTrue(response.context['is_admin'])

    def test_customer_show_order_customer(self):
        """Test customer accessing show_order_customer view"""
        self.mock_get_user_role.return_value = 'Customer'
        response = self.customer_client.get(reverse('order:show_order'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_order.html')
        self.assertTrue(response.context['is_customer'])

    def test_worker_show_order_worker(self):
        """Test worker accessing show_order_worker view"""
        self.mock_get_user_role.return_value = 'Worker'
        response = self.worker_client.get(reverse('order:show_order_worker'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_order.html')
        self.assertTrue(response.context['is_worker'])

    def test_admin_order_detail(self):
        """Test admin accessing order detail view"""
        self.mock_get_user_role.return_value = 'Admin'
        response = self.admin_client.get(reverse('order:order_detail', args=[self.order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_order_details.html')
        self.assertTrue(response.context['is_admin'])

    def test_customer_order_detail(self):
        """Test customer accessing their own order detail view"""
        self.mock_get_user_role.return_value = 'Customer'
        response = self.customer_client.get(reverse('order:order_detail', args=[self.order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_order_details.html')
        self.assertTrue(response.context['is_customer'])

    # aboba
    def test_worker_order_detail_with_valid_order(self):
        """Test worker accessing order detail view for ready order"""
        self.mock_get_user_role.return_value = 'Worker'
        self.order.status = self.delivered_status
        self.order.save()
        self.order_payment = OrderPayment.objects.create(walletAccount=self.customer_wallet_account, worker=self.worker,order=self.order)
        self.order.total = self.order.total + self.order_payment.delivery_fee
        self.order.save()
        self.order_payment.worker = self.worker
        self.order_payment.save()
        response = self.worker_client.get(reverse('order:order_detail', args=[self.order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_order_details.html')
        self.assertTrue(response.context['is_worker'])
    
    def test_customer_cancel_order(self):
        """Test customer cancelling their own order"""
        self.customer_client.force_login(self.customer.user)
        self.mock_get_user_role.return_value = 'Customer'
        response = self.customer_client.post(reverse('order:cancel_order', args=[self.order.id]))
        self.assertRedirects(response, reverse('order:order_detail', args=[self.order.id]))
        # Verify order status has been updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, self.cancelled_status)
'''
