from django import forms
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from main.models import Admin, Customer, Worker
from product.models import Product
from order.models import Order, OrderStatus
from administrator.forms import ProductForm
import json
import uuid
from cart.models import Cart


class AdminViewsTestCase(TestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(
        username='regular_user', password='password123'
        )
        self.customer_user = User.objects.create_user(
            username='customer_user', password='password123'
        )
        self.worker_user = User.objects.create_user(
            username='worker_user', password='password123'
        )
        self.admin_user = User.objects.create_user(
            username='admin_user', password='password123'
        )
        
        # Create role assignments (Customer, Worker, Admin) if needed
        self.customer = Customer.objects.create(user=self.customer_user)
        self.worker = Worker.objects.create(user=self.worker_user)
        self.admin = Admin.objects.create(user=self.admin_user)
        self.ready_status = OrderStatus.objects.create(id=uuid.uuid4(), status='ready')
        
        # Create Cart for the Order (OneToOneField to Cart)
        self.cart = Cart.objects.create(customer=self.customer)  # Fixed: Use Customer instance
        
        # Create a test OrderStatus
        self.order_status = OrderStatus.objects.create(id=uuid.uuid4(), status='not paid')
        
        # Create the Order with the cart and status
        self.order = Order.objects.create(
            cart=self.cart,
            status=self.order_status
        )
        
        # Create test products for tests that need them
        self.product1 = Product.objects.create(
            product_name='Test Product 1',
            stock=10,
            price=99.99,
            description='Test product 1 description'
        )
        
        self.product2 = Product.objects.create(
            product_name='Test Product 2',
            stock=20,
            price=199.99,
            description='Test product 2 description'
        )
        
        # Setup clients for testing
        self.admin_client = Client()
        self.regular_client = Client()
        self.customer_client = Client()
        self.worker_client = Client()
        
        # Log in clients
        self.admin_client.login(username='admin_user', password='password123')
        self.regular_client.login(username='regular_user', password='password123')
        self.customer_client.login(username='customer_user', password='password123')
        self.worker_client.login(username='worker_user', password='password123')

    # ---- Basic Access Tests ----
    
    def test_admin_dashboard_access(self):
        """Admin can access dashboard"""
        response = self.admin_client.get(reverse('administrator:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_admin'])
        self.assertTemplateUsed(response, 'dashboard.html')
        
        # Verify dashboard contains expected data
        self.assertIn('total_users', response.context)
        self.assertIn('users', response.context)
        self.assertIn('admin_user_ids', response.context)
        self.assertIn('customer_user_ids', response.context)
        self.assertIn('worker_user_ids', response.context)
    
    def test_product_dashboard_access(self):
        """Test that product dashboard is accessible to admin"""
        response = self.admin_client.get(reverse('administrator:product_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('products', response.context)
        self.assertEqual(list(response.context['products']), list(Product.objects.all().order_by('-id')))
        self.assertTrue(response.context['is_admin'])
    
    # ---- Authentication Flow Tests ----
    
    def test_security_anonymous_access_denied(self):
        """Anonymous users can't access admin areas"""
        client = Client()  # Anonymous client (not logged in)
        admin_urls = [
            reverse('administrator:dashboard'),
            reverse('administrator:product_dashboard'),
            reverse('administrator:create_product'),
            reverse('administrator:update_product', args=[self.product1.id]),
            reverse('administrator:delete_product', args=[self.product1.id]),
        ]
        
        for url in admin_urls:
            response = client.get(url)
            # Should redirect to login
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('/accounts/login/'))
    
    def test_security_role_based_access(self):
        """Different user roles have appropriate access levels"""
        # Admin-only URLs
        admin_only_urls = [
            reverse('administrator:create_product'),
            reverse('administrator:update_product', args=[self.product1.id]),
        ]
        
        # Test each client type
        for url in admin_only_urls:
            # Admin should have access
            admin_response = self.admin_client.get(url)
            self.assertEqual(admin_response.status_code, 200)
            
            # Non-admin users should be redirected
            for client in [self.regular_client, self.customer_client, self.worker_client]:
                response = client.get(url)
                self.assertEqual(response.status_code, 302)
                # Should redirect to no_permission
                self.assertEqual(response.url, reverse('administrator:no_permission'))
    
    # ---- Admin User Flow Tests ----
    
    def test_admin_user_management_flow(self):
        """Test the full flow of admin managing users"""
        # 1. Admin views all users in dashboard
        dashboard_response = self.admin_client.get(reverse('administrator:dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        
        # Verify all users are listed
        users_in_context = list(dashboard_response.context['users'])
        self.assertEqual(len(users_in_context), 4)  # All 4 test users
        
        # 2. Admin deletes a user
        delete_response = self.admin_client.post(
            reverse('administrator:delete_user', args=[self.regular_user.id])
        )
        self.assertEqual(delete_response.status_code, 302)
        self.assertEqual(delete_response.url, reverse('administrator:dashboard'))
        
        # 3. Verify user was deleted
        self.assertFalse(User.objects.filter(username='regular_user').exists())
        
        # 4. Verify admin activity was logged
        from administrator.models import AdminActivityLog
        latest_log = AdminActivityLog.objects.latest('id')
        self.assertEqual(latest_log.admin, self.admin)
        self.assertEqual(latest_log.action, f"Deleted user: {self.regular_user.username}")
    
    # ---- Order Processing Flow Tests ----
    
    def test_order_processing_flow(self):
        """Test the flow of admin processing orders"""
        # Admin processes an order
        process_response = self.admin_client.post(
            reverse('administrator:process_order', args=[self.order.id])
        )
        self.assertEqual(process_response.status_code, 302)
        
        # Verify order status was updated
        updated_order = Order.objects.get(id=self.order.id)
        self.assertEqual(updated_order.status.status, 'ready')
    
    # ---- Security Tests ----
    
    def test_csrf_protection(self):
        """Test CSRF protection on forms"""
        client = Client(enforce_csrf_checks=True)
        client.login(username='admin_user', password='password123')
        
        # Try to submit form without CSRF token
        response = client.post(
            reverse('administrator:create_product'),
            {'product_name': 'CSRF Test', 'stock': 10, 'price': 99.99}
        )
        self.assertEqual(response.status_code, 403)  # CSRF failure should return 403
    
    def test_direct_object_reference(self):
        """Test protection against insecure direct object references"""
        # Admin can update own product
        admin_update = self.admin_client.get(
            reverse('administrator:update_product', args=[self.product1.id])
        )
        self.assertEqual(admin_update.status_code, 200)
        
        # Try to access non-existent product ID
        non_existent_id = uuid.uuid4()
        admin_bad_update = self.admin_client.get(
            reverse('administrator:update_product', args=[non_existent_id])
        )
        self.assertEqual(admin_bad_update.status_code, 404)
    
    def test_authorization_checks(self):
        """Test that authorization is checked before performing actions"""
        # Regular user attempts to delete a product (should be rejected)
        initial_count = Product.objects.count()
        delete_attempt = self.regular_client.post(
            reverse('administrator:delete_product', args=[self.product1.id])
        )
        
        # Should redirect to no_permission
        self.assertEqual(delete_attempt.status_code, 302)
        self.assertEqual(Product.objects.count(), initial_count)  # Count should not change
    
    def test_json_endpoint_security(self):
        """Test that JSON endpoints have proper access controls"""
        # Admin can access all_product JSON endpoint
        admin_response = self.admin_client.get(reverse('administrator:all_product'))
        self.assertEqual(admin_response.status_code, 200)
        
        # Verify JSON structure
        admin_data = json.loads(admin_response.content)
        self.assertIn('products', admin_data)
        self.assertEqual(len(admin_data['products']), 2)  # Two test products
        
        # Anonymous user cannot access JSON endpoint
        anon_client = Client()
        anon_response = anon_client.get(reverse('administrator:all_product'))
        self.assertEqual(anon_response.status_code, 302)  # Should redirect to login
    
    # ---- Form Validation Tests ----
    
    def test_product_form_validation(self):
        """Test that form validation works properly"""
        # Test invalid data (negative stock)
        invalid_data = {
            'product_name': 'Invalid Product',
            'stock': -5,  # Negative stock should be invalid
            'price': 100,
            'description': 'Test invalid product'
        }
        response = self.admin_client.post(
            reverse('administrator:create_product'),
            data=invalid_data
        )
        
        # Form should be invalid and return to the form page (not redirect)
        self.assertEqual(response.status_code, 200)
        
        # Check that form has errors
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)
        
        # Product should not be created
        self.assertFalse(Product.objects.filter(product_name='Invalid Product').exists())

    def test_no_permission_view_status(self):
        """No permission view returns 403 status code"""
        response = self.regular_client.get(reverse('administrator:no_permission'))
        self.assertEqual(response.status_code, 403)

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError("Stock cannot be negative")
        return stock